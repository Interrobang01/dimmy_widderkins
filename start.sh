#!/bin/bash

#parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )

#cd "$parent_path"

# Make sure we clean up processes on exit
#cleanup() {
#  echo "Cleaning up processes..."
#  pkill -f "ollama run qwen3:0.6b" || true
#  pkill -f "python3 bot.py" || true
#}

# Set up trap to call cleanup function when script exits
#trap cleanup EXIT

# Start the Brook server
#(source ~/.profile && source ~/.bashrc && $(which bun || echo "$HOME/.bun/bin/bun") brook_server.ts) &

# Start the bot
VENV_PATH="/home/randy/firmament/firmament"
PYTHON_SCRIPT="/home/randy/firmament/bot.py"
"${VENV_PATH}/bin/python3" "${PYTHON_SCRIPT}"
