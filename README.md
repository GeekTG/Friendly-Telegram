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
`sudo apt install python3.7 git dialog`

3. Install optional modular dependencies
`sudo apt install python3.7-dev neofetch speedtest-cli`

### Configuring the userbot

1. Clone the source code
`cd`
`git clone https://github.com/penn5/friendly-telegram`

2. Install requirements
`python3.7 -m pip install -r friendly-telegram/requirements.txt`

3.  Follow the instructions written [here](https://core.telegram.org/api/obtaining_api_id "here") to get your API key/hash and ID

4. Run the configuration script
`cd`
`python3.7 -m friendly-telegram --setup`

5. On the newly opened menu, select "API Key/hash and ID"
When prompted, enter your API key/hash and ID

### Launching the bot

`python3.7 -m friendly-telegram`

## Usage

Try typing .help in any Telegram chat while the bot is running
