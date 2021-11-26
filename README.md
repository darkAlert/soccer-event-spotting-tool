# SoccerEventSpottingTool
SoccerEventSpottingTool is a tool for spotting and annotating soccer events



Установка под MacOS:

1) поставить brew:
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"

2) поставить python:
brew install python

3) поставить git:
brew install git

4) установить pipenv:
brew install pipenv

5) установить tk:
brew install python-tk

6) скачать репозиторий с гита:
mkdir ~/builds
cd ~/builds
git clone https://github.com/darkAlert/soccer-event-spotting-tool.git
cd  soccer-event-spotting-tool

7) Установить зависимости через виртуальное окружение:
pipenv install -r requirements.txt --python 3

8) Теперь можно запускать (из папки ~/builds/soccer-event-spotting-tool):
pipenv run python3 run_player.py --video_dir /path/to/video/dir