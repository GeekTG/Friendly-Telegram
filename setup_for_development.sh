#!/bin/sh
# Not copyright, it's from documentation
python3.7 -m pip install --user flake8 flake8-print flake8-quotes
git config --bool flake8.strict true
git config --bool flake8.lazy true
python3.7 -m flake8 --install-hook git
