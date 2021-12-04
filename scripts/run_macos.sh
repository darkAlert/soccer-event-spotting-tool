#!/bin/sh

usage() {
  echo "usage: run_macos.sh
   [--video-dir=VIDEO_DIR] [-cvmp] [--enable_cvmp]"
}

# Parse input arguments:
while [ $# -gt 0 ]; do
  case "$1" in
    -h)
      usage
      exit 0
      ;;
    *)
      # All other arguments will be passed to run_player.py
      INFER_ARGS+=" ${1}"
  esac
  shift
done


cd ~/builds/soccer-event-spotting-tool

# Update:
git checkout .
git pull

# Run:
pipenv run python3 run_player.py ${INFER_ARGS}
