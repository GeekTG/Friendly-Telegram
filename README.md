# friendly-telegram userbot

Hey, welcome to our userbot!

## But how do I set it up?

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
sudo apt install python3-dev libwebp-dev libz-dev libjpeg-dev
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
python3 -m pip install -r friendly-telegram/requirements.txt
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
pkg install git python-dev libjpeg-turbo-dev zlib-dev libwebp-dev libffi-dev build-essential dialog neofetch
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

### Installing python 3 and other dependencies 

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
 
### Configuring the Userbot

1. Clone the source and install requirements

```
# Clone the source
git clone https://github.com/penn5/friendly-telegram
cd friendly-telegram
# Install the requirements 
pip3 install cryptg
pip3 install -r requirements.txt
```
2.  Follow the instructions written [here](https://core.telegram.org/api/obtaining_api_id "here") to get your API key/hash and ID

3. Run the configuration script
`python3 -m friendly-telegram --setup`

 ##### On the newly opened menu, select "API Key/hash and ID". When prompted, enter your API key/hash and ID

4. Launching the bot 
```
cd ~/friendly-telegram
python3 -m friendly-telegram
```

### Web hosting services

These are basically just Linux. They will work with some effort to get the API token and session file over.
