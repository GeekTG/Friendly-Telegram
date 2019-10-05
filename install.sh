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

# Modified version of https://stackoverflow.com/a/3330834/5509575
sp='/-\|'
spin() {
    printf '\b%.1s' "$sp"
    sp=${sp#?}${sp%???}
}
endspin() {
    printf '\r%s\n' "$@"
}

##############################################################################

# Banner generated with following command:
# pyfiglet -f smslant -w 50 friendly telegram | sed 's/\\/\\\\/g' | sed 's/"/\\"/g' | sed 's/`/\\`/g' | sed 's/^/printf "%s\\n" "/m;s/$/"/m'
# Ugly, I know.

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

printf '%s\n' "The process takes around 1-3 minutes"
printf '%s' "Installing now...  "

##############################################################################

spin

if [ ! x"" = x"$DYNO" ]; then
  # We are running in a heroku dyno, time to get ugly!
  git clone https://github.com/heroku/heroku-buildpack-python || { endspin "Bootstrap download failed!"; exit 1; }
  spin
  rm -rf .heroku .cache .profile.d requirements.txt runtime.txt .env
  mkdir .cache .env
  echo "python-3.7.4" > runtime.txt
  echo "pip" > requirements.txt
  spin
  STACK=heroku-18 bash heroku-buildpack-python/bin/compile /app /app/.cache /app/.env || \
      { endspin "Bootstrap install failed!"; exit 1; }
  spin
  rm -rf .cache
  export PATH="/app/.heroku/python/bin:$PATH"  # Prefer the bootstrapped python, incl. pip, over the system one.
fi

if [ -d "friendly-telegram/friendly-telegram" ]; then
  cd friendly-telegram || { endspin "Failed to chdir"; exit 6; }
  DIR_CHANGED="yes"
fi
if [ -f ".setup_complete" ]; then
  PYVER=""
  if echo "$OSTYPE" | grep -qE '^linux-gnu.*'; then
    PYVER="3"
  fi
  endspin
  "python$PYVER" -m friendly-telegram "$@"
  exit $?
elif [ "$DIR_CHANGED" = "yes" ]; then
  cd ..
fi

##############################################################################

if echo "$OSTYPE" | grep -qE '^linux-gnu.*'; then
  PKGMGR="apt-get install -y"
  if [ ! "$(whoami)" = "root" ]; then
    # Relaunch as root, preserving arguments
    if command -v sudo >/dev/null; then
      endspin "Restarting as root..."
      sudo "$SHELL" -c '$SHELL <('"$(command -v curl >/dev/null && echo 'curl -Ls' || echo 'wget -qO-')"' https://git.io/JeOXn) '"$*"
      exit $?
    else
      PKGMGR="true"
    fi
  else
    spin
    apt-get update >/dev/null
  fi
  PYVER="3"
elif [ "$OSTYPE" = "linux-android" ]; then
  spin
  apt-get update >/dev/null
  PKGMGR="apt-get install -y"
  PYVER=""
elif echo "$OSTYPE" | grep -qE '^darwin.*'; then
  if ! command -v brew >/dev/null; then
    spin
    ruby <(curl -fsSk https://raw.github.com/mxcl/homebrew/go)
  fi
  PKGMGR="brew install"
  PYVER="3"
else
  endspin "Unrecognised OS. Please follow https://friendly-telegram.github.io/installing_advanced"
  exit 1
fi
spin

##############################################################################

$PKGMGR "python$PYVER" git >/dev/null || { endspin "Core install failed."; exit 2; }
spin

if echo "$OSTYPE" | grep -qE '^linux-gnu.*'; then
  $PKGMGR "python$PYVER-dev" >/dev/null
  spin
  $PKGMGR "python$PYVER-pip" >/dev/null
  spin
  $PKGMGR build-essential libwebp-dev libz-dev libjpeg-dev libffi-dev libcairo2 libopenjp2-7 libtiff5 libcairo2-dev >/dev/null
elif [ "$OSTYPE" = "linux-android" ]; then
  $PKGMGR libjpeg-turbo libwebp libffi libcairo build-essential >/dev/null
elif echo "$OSTYPE" | grep -qE '^darwin.*'; then
  $PKGMGR jpeg webp >/dev/null
fi
spin

$PKGMGR neofetch dialog >/dev/null
spin

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
${SUDO_CMD}git clone -q https://github.com/friendly-telegram/friendly-telegram || { endspin "Clone failed."; exit 3; }
spin
cd friendly-telegram || { endspin "Failed to chdir"; exit 7; }
# shellcheck disable=SC2086
${SUDO_CMD}"python$PYVER" -m pip -q install cryptg --user --no-warn-script-location --disable-pip-version-check 2>/dev/null >/dev/null
spin
# shellcheck disable=SC2086
${SUDO_CMD}"python$PYVER" -m pip -q install -r requirements.txt --user --no-warn-script-location --disable-pip-version-check || { endspin "Requirements failed!"; exit 4; }
spin
touch .setup_complete
endspin
# shellcheck disable=SC2086,SC2015
${SUDO_CMD}"python$PYVER" -m friendly-telegram && python$PYVER -m friendly-telegram "$@" || { echo "Python scripts failed"; exit 5; }
