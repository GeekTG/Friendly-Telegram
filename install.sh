if [ ! "$(whoami)" = "root" ]; then
  echo "Please run as root."
  exit 1
fi

if [ "$OSTYPE" = "linux-gnu" ]; then
  PKGMGR="apt"
  apt update
  PYVER="3"
elif [ "$OSTYPE" = "linux-android" ]; then
  PKGMGR="pkg"
  PYVER=""
elif [ "$OSTYPE" = "darwin"* ]; then
  echo "macOS not yet supported by automated install script. Please go to https://github.com/penn5/friendly-telegram/#mac-os-x"
  exit 1
else
  echo "Unrecognised OS. Please follow https://github.com/penn5/friendly-telegram/blob/master/README.md"
  exit 1
fi

"$PKGMGR" install "python$PYVER" git || { echo "Core install failed."; exit 2; }


if [ ! "$OSTYPE" = "linux-android" ]; then
  "$PKGMGR" install "python$PYVER-dev" || echo "Python-dev install failed."
  "$PKGMGR" install build-essential libwebp-dev libz-dev libjpeg-dev libffi-dev libcairo2-dev || echo "Stickers install failed."
  "$PKGMGR" install neofetch || echo "Utilities install failed."
  "$PKGMGR" install dialog || echo "UI install failed."
else
  "$PKGMGR" install libjpeg-turbo libwebp libffi libcairo build-essential dialog neofetch || echo "Optional installation failed."
fi

git clone https://github.com/penn5/friendly-telegram || { echo "Clone failed."; exit 3; }
cd friendly-telegram
"python$PYVER" -m pip install cryptg || echo "Cryptg failed"
"python$PYVER" -m pip install -r requirements.txt || { echo "Requirements failed!"; exit 4; }
"python$PYVER" -m friendly-telegram && python$PYVER -m friendly-telegram || { echo "Python scripts failed"; return 5; }
