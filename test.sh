#!/bin/bash
# CI test script

pip install flake8 flake8-print flake8-quotes
flake8 --statistics
exit $?
