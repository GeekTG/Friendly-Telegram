# Configuration

The configuration interface is a little difficult to navigate. This attempts to document it

## Entering configuration

`python -m friendly-telegram --setup`

## Operating modes

The first thing to understand is that it has two modes of operation.

- Terminal mode
  - Black-and-white
  - Uses numbers to select which item in the menu you want
- Graphical mode
  - Coloured
  - Uses arrow keys and tabs to select items

In terminal mode, you can press the number 0 to go back, or another number to select what option you want.

In graphical mode, press tab to select the cancel button at the bottom right, and press enter to cancel.
Pressing up and down arrow keys select the item to select, and enter selects the item

## Setting API keys

API keys allow communication with the Telegram servers. You can get an API key from [the Telegram website](https://core.telegram.org/api/obtaining_api_id "the Telegram website"). In the configurator, you have to go to "API Token and ID" to set it.

Without an API key, you cannot use friendly-telegram. When requesting an API key, you can enter any details. No-one checks it.

## Configuring modules

This userbot is highly modular and each module can be configured individually, or disabled entirely.
If you disable a module, it will not be loaded at startup. To re-enable it, you have to edit the configuration and restart the userbot.

Module settings are stored **inside your Telegram account**. To debug this, search for a chat named "friendly-{id}-data". It contains a JSON dump of the database. This includes config as well as other data such as your AFK status. **You should never share this message or add anyone to that chat**. It contains personal data such as API keys. 

To set a module config, select it and enter the value. The easiest way to check the valid values is to read the source, but if it is an api token its usually an api token.

Note that if you change the config on one computer while hosting on another, you need to restart the bot.
