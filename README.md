# ⚠️⚠️⚠️ Warning ⚠️⚠️⚠️

## This code as been relicensed to AGPL v3

This has been authorised by all copyright holders. All previous licenses have been revoked! Nobody may copy or use this project without following the terms of the AGPLv3, as set out in the LICENSE file.

# ANYONE STEALING MY CODE WILL BE DMCA'd!!!

# friendly-telegram userbot

Hey, welcome to our userbot!

## But how do I set it up?

TL;DR run on a Linux PC or in Termux:
`$SHELL <(curl -Ls https://raw.githubusercontent.com/penn5/friendly-telegram/master/install.sh)`

All of the setup instructions are in this README, read carefully!

First of all, this bot requires Python 3 (minimum 3.5) and a modern-ish OS (preferably Linux-based)

Step by step explanation:

### Installing Python 3 and required packages

1. Update package list
` sudo apt update`

2. Install required packages
`sudo apt install python3 python3-pip git`

3. Install optional modular dependencies (required for some modules)
```
# Pillow for stickers/kang
sudo apt install python3-dev libwebp-dev libz-dev libjpeg-dev libopenjp2-7 libtiff5 libcairo2
# Utilities
sudo apt install neofetch
# UI
sudo apt install dialog
```

### Configuring the userbot

1. Clone the source code
```
cd
git clone https://github.com/penn5/friendly-telegram
cd friendly-telegram
```

2. Install requirements
```
python3 -m pip install cryptg
python3 -m pip install -r requirements.txt
```

3.  Follow the instructions written [here](https://core.telegram.org/api/obtaining_api_id "here") to get your API key/hash and ID

4. Run the configuration script
`python3 -m friendly-telegram --setup`

5. On the newly opened menu, select "API Key/hash and ID"
When prompted, enter your API key/hash and ID

### Launching the bot

```
cd ~/friendly-telegram
python3 -m friendly-telegram
```

## Usage

Try typing .help in any Telegram chat while the bot is running

## OS Quirks

### Android

Use Termux
```
pkg install git python libjpeg-turbo zlib libwebp libffi build-essential dialog neofetch
git clone https://github.com/penn5/friendly-telegram
cd friendly-telegram
pip install cryptg
pip install -r requirements.txt
# For setup
python -m friendly-telegram --setup
# And again for actual execution
python -m friendly-telegram
```
Make sure to enable the wakelock from Termux notification, especially on MIUI

### Windows

- All terminal related features don't work. I'll fix it later.

### Mac OS X

#### Installing python 3 and other dependencies 

1. Setup homebrew
`ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"`

2. Install required packages
`brew install python3  git`

3. Install optional modular dependencies (required for some modules)
```
# Utilities
brew install neofetch
# UI
brew install dialog
```
##### Pillow for stickers/kang (You'll need to manually build these)
 - libwebp -> https://github.com/webmproject/libwebp
 - libjpeg -> https://github.com/LuaDist/libjpeg
 
##### Refer above (to the Linux section) for configuring and launching the userbot.

### Web hosting services

#### Heroku

Run as usual but with `--heroku` argument and it will guide you through upload. Note that if it seems to have hung, don't kill it. It's still running.

#### Others

These are basically just Linux. They will work with some effort to get the API token and session file over.

### Windows

#### Tested on Windows 10

1. Install python3 from https://python.org

2. Download this project

3. Open a powershell window in the root of this project

4. Run
`python -m pip install -r requirements.txt`

5. Run
`python -m friendly-telegram`

6. Enter your API hash & ID from my.telegram.org

7. Rerun
`python -m friendly-telegram`

8. Enter you phone number

9. (optionally) if you want to install to Heroku, download git-scm, selecting the recommended options in the installer

10. (optionally) if you want to install to Heroku, run
`python -m friendly-telegram --heroku`
