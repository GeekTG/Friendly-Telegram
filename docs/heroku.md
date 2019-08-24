# Heroku hosting support

Heroku is fully supported. Setup is extremely simple

1. First follow the instructions to set up the bot in [installing.md](https://github.com/penn5/friendly-telegram/blob/master/docs/installing.md "installing.md") and ensure the bot works

2. Append `--heroku` to the end of the command used to start the bot. For example:
`python -m friendly-telegram` -> `python -m friendly-telegram --heroku`

`python3.7 -m friendly-telegram` -> `python3.7 -m friendly-telegram --heroku`

Alternatively, if your OS is supported by the setup script, run:
`"$SHELL" -c '$SHELL <(curl -Ls https://raw.githubusercontent.com/penn5/friendly-telegram/master/install.sh) --heroku'`
to automatically push to heroku with a one-liner
