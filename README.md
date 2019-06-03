# friendly-telegram userbot

Hey, welcome to our userbot!

## But how do I set it up?

All of the setup instructions are in this README, read carefully!

First of all, this bot requires Python 3.7 and a modern OS (preferably Linux-based)

Step by step explanation:

### Installing Python 3.7 and required packages

1. Update package list
` sudo apt update`

2. Install required packages
`sudo apt install python3.7 python3.7-dev dialog git neofetch`

### Configuring the userbot

1. Clone the source code
`cd ~/`
`git clone https://github.com/penn5/friendly-telegram`

2. Install requirements
`cd friendly-telegram`
`python3.7 -m pip install -r requirements.txt`

3.  Follow the instructions written [here](https://core.telegram.org/api/obtaining_api_id "here") to get your API key/hash and ID

4. Run the configuration script
`python3.7 -m friendly-telegram --setup`

5. On the newly opened menu, select "API Key/hash and ID"
When prompted, enter your API key/hash and ID

### Launching the bot

`python3.7 -m friendly-telegram`

## Usage

Try typing .help in any Telegram chat while the bot is running
