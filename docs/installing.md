# Installation

### There are 2 methods to install - manual or scripted

## Scripted method

It's very simple - paste this command into a Linux terminal (on Android use termux): ```"$SHELL" -c '$SHELL <(curl -Ls https://raw.githubusercontent.com/friendly-telegram/friendly-telegram/master/install.sh)'```

Or, for Windows, paste this command in a command prompt or Powershell window: ```Invoke-Expression((New-Object Net.WebClient).DownloadString("https://raw.githubusercontent.com/friendly-telegram/friendly-telegram/master/install.ps1"))```

## Manual method

This is split into several methods, one for each supported OS.

### Debian-like Linux

1. Update package list
` sudo apt update`

2. Install required packages
`sudo apt install python3 python3-pip git`

3. Install optional modular dependencies (required for some modules)
```
# Pillow for stickers/kang
sudo apt install python3-dev libwebp-dev libz-dev libjpeg-dev libopenjp2-7 libtiff5
# Cairo for animated stickers
sudo apt install libffi-dev libcairo2
# Utilities
sudo apt install neofetch
# UI
sudo apt install dialog
```

4. Clone the source code
```
cd
git clone https://github.com/friendly-telegram/friendly-telegram
cd friendly-telegram
```

5. Install requirements
```
python3 -m pip install cryptg
python3 -m pip install -r requirements.txt
```

6. Follow the instructions written [here](https://core.telegram.org/api/obtaining_api_id "here") to get your API key/hash and ID

7. Run the configuration script
`python3 -m friendly-telegram --setup`

8. On the newly opened menu, select "API Key/hash and ID"
When prompted, enter your API key/hash and ID

9. Launch the bot:
```
cd ~/friendly-telegram
python3 -m friendly-telegram
```

### Termux

```
pkg install git python libjpeg-turbo zlib libwebp libffi libcairo build-essential dialog neofetch
git clone https://github.com/friendly-telegram/friendly-telegram
cd friendly-telegram
pip install cryptg
pip install -r requirements.txt
# For setup
python -m friendly-telegram --setup
# And again for actual execution
python -m friendly-telegram
```

## Windows

1. Install Git from [the website](https://git-scm.com "the website"). **Make sure to add Git to the PATH**

2. Install Python from [the website](https://www.python.org/downloads/windows "the website"). **Make sure to add Python to the PATH**

3. Open a Windows Powershell window [tutorial](https://www.google.com/url?sa=t&rct=j&q=&esrc=s&source=web&cd=3&cad=rja&uact=8&ved=2ahUKEwijicaXspvkAhVDaFAKHT26DHgQFjACegQIChAG&url=https%3A%2F%2Fwww.isunshare.com%2Fwindows-10%2F5-ways-to-open-windows-powershell-in-windows-10.html "tutorial"). 

4. Follow the instructions written [here](https://core.telegram.org/api/obtaining_api_id "here") to get your API key/hash and ID

5. Type:
```
git clone https://github.com/friendly-telegram/friendly-telegram
cd friendly-telegram
python3 -m pip install -r requirements.txt
python3 -m friendly-telegram
```

6. Enter the API hash and ID when prompted (note the menu is a little archeic on Windows, read everything the program outputs to get a better understanding)

7. Type `python -m friendly-telegram` once more to activate the bot

# Mac OS X

1. Install Homebrew
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

4. Manually build the following repos (only required for sticker support):
 - libwebp -> https://github.com/webmproject/libwebp
 - libjpeg -> https://github.com/LuaDist/libjpeg

5. Follow the instructions written [here](https://core.telegram.org/api/obtaining_api_id "here") to get your API key/hash and ID

6. Type:
```
git clone https://github.com/friendly-telegram/friendly-telegram
cd friendly-telegram
python -m pip install -r requirements.txt
python -m friendly-telegram
```

7. Enter your API hash and ID when prompted

8. Type `python -m friendly-telegram` once more to activate the bot
