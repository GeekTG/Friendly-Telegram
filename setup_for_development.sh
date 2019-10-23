#!/bin/sh
# Not copyright, it's from documentation

git config --bool flake8.strict true
git config --bool flake8.lazy true
flake8 --install-hook git
