#!/bin/sh

/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"

brew install python
brew install git
brew install pipenv
brew install python-tk

mkdir ~/builds
cd ~/builds
git clone https://github.com/darkAlert/soccer-event-spotting-tool.git
cd  soccer-event-spotting-tool

pipenv install -r requirements.txt --python 3


pipenv run python3 run_player.py