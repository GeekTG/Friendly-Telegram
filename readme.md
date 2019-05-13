# friendly-telegram userbot

Hey, welcome to our userbot!

This project is still a heavy WIP(be warned!)

## But how do I set it up?

All of the setup instructions are in this readme, read carefully!

First of all, this bot requires python 3.7 and Ubuntu 16.04 or higher

Step by step explanation:

### Installing Python 3.7 and required packages

1.  Add the deadsnakes PPA  
    `sudo add-apt-repository ppa:deadsnakes/ppa`

2. Update package list  
` sudo apt update`

3. Install required packages  
`sudo apt install python3.7 dialog python3-dialog git`

4. Set Python 3.7 as default Python  
`sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.7 1`

### Configuring the userbot

1. Clone the source code  
`cd ~/`  
`git clone https://github.com/penn5/friendly-telegram`

2. Install requirements  
`cd friendly-telegram`  
`pip3 install -r requirements.txt`

3.  Follow the instructions written [here](https://core.telegram.org/api/obtaining_api_id "here") to get your API key/hash and ID

4. Run the configuration script  
`python3 configurator.py`

5. On the newly opened menu, select "API Key/hash and ID"
When prompted, enter your API key/hash and ID

6. Finally, run the bot!  
`cd ..`  
`python3 -m friendly-telegram`

