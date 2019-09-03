if [ "$OSTYPE" = "linux-gnu" ]; then
  if [ ! "$(whoami)" = "root" ]; then
    # Relaunch as root, preserving arguments
    sudo "$SHELL" -c '$SHELL <(curl -Ls https://raw.githubusercontent.com/friendly-telegram/friendly-telegram/master/install.sh) '"$@"
    exit $?
  fi
  PKGMGR="apt"
  apt update
  PYVER="3.7"
elif [ "$OSTYPE" = "linux-android" ]; then
  PKGMGR="pkg"
  PYVER=""
elif [ "$OSTYPE" = "darwin"* ]; then
  echo "macOS not yet supported by automated install script. Please go to https://github.com/friendly-telegram/friendly-telegram/#mac-os-x"
  exit 1
else
  echo "Unrecognised OS. Please follow https://github.com/friendly-telegram/friendly-telegram/blob/master/README.md"
  exit 1
fi

"$PKGMGR" install "python$PYVER" git || { echo "Core install failed."; exit 2; }


if [ ! "$OSTYPE" = "linux-android" ]; then
  "$PKGMGR" install "python$PYVER-dev" || echo "Python-dev install failed."
  "$PKGMGR" install build-essential libwebp-dev libz-dev libjpeg-dev libffi-dev libcairo2 libopenjp2-7 libtiff5 libcairo2-dev || echo "Stickers install failed."
  "$PKGMGR" install neofetch || echo "Utilities install failed."
  "$PKGMGR" install dialog || echo "UI install failed."
else
  "$PKGMGR" install libjpeg-turbo libwebp libffi libcairo build-essential dialog neofetch || echo "Optional installation failed."
fi

if [ ! x"$SUDO_USER" = x"" ]; then
  SUDO_CMD="sudo -u $SUDO_USER "
else
  SUDO_CMD=""
fi

[ -d friendly-telegram ] || ${SUDO_CMD}rm -rf friendly-telegram
${SUDO_CMD}git clone https://github.com/friendly-telegram/friendly-telegram || { echo "Clone failed."; exit 3; }
cd friendly-telegram
${SUDO_CMD}"python$PYVER" -m pip install cryptg || echo "Cryptg failed"
${SUDO_CMD}"python$PYVER" -m pip install -r requirements.txt || { echo "Requirements failed!"; exit 4; }
${SUDO_CMD}"python$PYVER" -m friendly-telegram && python$PYVER -m friendly-telegram $@ || { echo "Python scripts failed"; exit 5; }
