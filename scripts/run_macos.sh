#!/bin/sh

cd ~/builds/soccer-event-spotting-tool

git checkout .
git pull
pipenv run python3 run_player.py
