#!/bin/bash

#    Friendly Telegram (telegram userbot)
#    Copyright (C) 2018-2019 The Authors

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.

#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

if [ ! -n "$BASH" ]; then
  echo "Non-bash shell detected, fixing..."
  bash -c '. <('"$(command -v curl >/dev/null && echo 'curl -Ls' || echo 'wget -qO-')"' https://git.io/JeOXn) '"$*"
  exit $?
fi

# Modified version of https://stackoverflow.com/a/3330834/5509575
sp='/-\|'
spin() {
  printf '\b%.1s' "$sp"
  sp=${sp#?}${sp%???}
}
endspin() {
  printf '\r%s\n' "$@"
}

runin() {
  # Runs the arguments and spins once per line of stdout (tee'd to logfile), also piping stderr to logfile
  { "$@" 2>>../ftg-install.log || return $?; } | while read -r line; do
    spin
    printf "%s\n" "$line" >> ../ftg-install.log
  done
}

runout() {
  # Runs the arguments and spins once per line of stdout (tee'd to logfile), also piping stderr to logfile
  { "$@" 2>>ftg-install.log || return $?; } | while read -r line; do
    spin
    printf "%s\n" "$line" >> ftg-install.log
  done
}

errorin() {
  endspin "$@"
  cat ../ftg-install.log
}
errorout() {
  endspin "$@"
  cat ftg-install.log
}

# Banner generated with following command:
# pyfiglet -f smslant -w 50 friendly telegram | sed 's/\\/\\\\/g' | sed 's/"/\\"/g' | sed 's/`/\\`/g' | sed 's/^/printf "%s\\n" "/m;s/$/"/m'
# Ugly, I know.

banner() {
  clear
  clear
  printf '%s\n' "   ___    _             ____    "
  printf '%s\n' "  / _/___(_)__ ___  ___/ / /_ __"
  printf '%s\n' " / _/ __/ / -_) _ \\/ _  / / // /"
  printf '%s\n' "/_//_/ /_/\\__/_//_/\\_,_/_/\\_, / "
  printf '%s\n' "                         /___/  "
  printf '%s\n' "  __      __                      "
  printf '%s\n' " / /____ / /__ ___ ________ ___ _ "
  printf '%s\n' "/ __/ -_) / -_) _ \`/ __/ _ \`/  ' \\"
  printf '%s\n' "\\__/\\__/_/\\__/\\_, /_/  \\_,_/_/_/_/"
  printf '%s\n' "             /___/                "
  printf '%s\n' ""
}

##############################################################################

banner
printf '%s\n' "The process takes around 3-7 minutes"
printf '%s' "Installing now...  "

##############################################################################

spin

touch ftg-install.log
if [ ! x"$SUDO_USER" = x"" ]; then
  chown "$SUDO_USER:" ftg-install.log
fi

if [ ! x"" = x"$DYNO" ] && ! command -v python >/dev/null; then
  # We are running in a heroku dyno without python, time to get ugly!
  runout git clone https://github.com/heroku/heroku-buildpack-python || { endspin "Bootstrap download failed!"; exit 1; }
  rm -rf .heroku .cache .profile.d requirements.txt runtime.txt .env
  mkdir .cache .env
  echo "python-3.7.5" > runtime.txt
  echo "pip" > requirements.txt
  STACK=heroku-18 runout bash heroku-buildpack-python/bin/compile /app /app/.cache /app/.env || \
      { endspin "Bootstrap install failed!"; exit 1; }
  rm -rf .cache
  export PATH="/app/.heroku/python/bin:$PATH"  # Prefer the bootstrapped python, incl. pip, over the system one.
fi

if [ -d "friendly-telegram/friendly-telegram" ]; then
  cd friendly-telegram || { endspin "Failed to chdir"; exit 6; }
  DIR_CHANGED="yes"
fi
if [ -f ".setup_complete" ] || [ -d "friendly-telegram" -a ! x"" = x"$DYNO" ]; then
  # If ftg is already installed by this script, or its in Heroku and installed
  PYVER=""
  if echo "$OSTYPE" | grep -qE '^linux-gnu.*'; then
    PYVER="3"
  fi
  endspin "Existing installation detected"
  clear
  banner
  "python$PYVER" -m friendly-telegram "$@"
  exit $?
elif [ "$DIR_CHANGED" = "yes" ]; then
  cd ..
fi

##############################################################################

echo "Installing..." > ftg-install.log

if echo "$OSTYPE" | grep -qE '^linux-gnu.*' && [ -f '/etc/debian_version' ]; then
  PKGMGR="apt-get install -y"
  if [ ! "$(whoami)" = "root" ]; then
    # Relaunch as root, preserving arguments
    if command -v sudo >/dev/null; then
      endspin "Restarting as root..."
      echo "Relaunching" >>ftg-install.log
      sudo "$BASH" -c '. <('"$(command -v curl >/dev/null && echo 'curl -Ls' || echo 'wget -qO-')"' https://git.io/JeOXn) '"$*"
      exit $?
    else
      PKGMGR="true"
    fi
  else
    runout apt-get update  # Not essential
  fi
  PYVER="3"
elif echo "$OSTYPE" | grep -qE '^linux-gnu.*' && [ -f '/etc/arch-release' ]; then
  PKGMGR="pacman -Sy"
  if [ ! "$(whoami)" = "root" ]; then
    # Relaunch as root, preserving arguments
    if command -v sudo >/dev/null; then
      endspin "Restarting as root..."
      echo "Relaunching" >>ftg-install.log
      sudo "$BASH" -c '. <('"$(command -v curl >/dev/null && echo 'curl -Ls' || echo 'wget -qO-')"' https://git.io/JeOXn) '"$*"
      exit $?
    else
      PKGMGR="true"
    fi
  fi
  PYVER="3"
elif echo "$OSTYPE" | grep -qE '^linux-android.*'; then
  runout apt-get update
  PKGMGR="apt-get install -y"
  PYVER=""
elif echo "$OSTYPE" | grep -qE '^darwin.*'; then
  if ! command -v brew >/dev/null; then
    ruby <(curl -fsSk https://raw.github.com/mxcl/homebrew/go)
  fi
  PKGMGR="brew install"
  PYVER="3"
else
  endspin "Unrecognised OS. Please follow https://friendly-telegram.github.io/installing_advanced"
  exit 1
fi

##############################################################################

runout $PKGMGR "python$PYVER" git || { errorout "Core install failed."; exit 2; }

if echo "$OSTYPE" | grep -qE '^linux-gnu.*'; then
  runout $PKGMGR "python$PYVER-dev"
  runout $PKGMGR "python$PYVER-pip"
  runout $PKGMGR build-essential libwebp-dev libz-dev libjpeg-dev libffi-dev libcairo2 libopenjp2-7 libtiff5 libcairo2-dev
elif echo "$OSTYPE" | grep -qE '^linux-android.*'; then
  runout $PKGMGR libjpeg-turbo libwebp libffi libcairo build-essential libxslt libiconv
elif echo "$OSTYPE" | grep -qE '^darwin.*'; then
  runout $PKGMGR jpeg webp
fi

runout $PKGMGR neofetch dialog

##############################################################################

SUDO_CMD=""
if [ ! x"$SUDO_USER" = x"" ]; then
  if command -v sudo>/dev/null; then
    SUDO_CMD="sudo -u $SUDO_USER "
  fi
fi

# shellcheck disable=SC2086
${SUDO_CMD}rm -rf friendly-telegram
# shellcheck disable=SC2086
runout ${SUDO_CMD}git clone https://github.com/friendly-telegram/friendly-telegram || { errorout "Clone failed."; exit 3; }
cd friendly-telegram || { endspin "Failed to chdir"; exit 7; }
# shellcheck disable=SC2086
runin ${SUDO_CMD}"python$PYVER" -m pip install --upgrade pip --user
# shellcheck disable=SC2086
runin ${SUDO_CMD}"python$PYVER" -m pip install -r optional-requirements.txt --user --no-warn-script-location --disable-pip-version-check || true
# shellcheck disable=SC2086
runin ${SUDO_CMD}"python$PYVER" -m pip install -r mandatory-requirements.txt --user --no-warn-script-location --disable-pip-version-check || { errorin "Requirements failed!"; exit 4; }
touch .setup_complete
endspin "Installation successful. Launching setup interface..."
rm -f ../ftg-install.log
# shellcheck disable=SC2086,SC2015
${SUDO_CMD}"python$PYVER" -m friendly-telegram "$@" || { echo "Python scripts failed"; exit 5; }
