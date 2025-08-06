#!/bin/bash

parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )

cd "$parent_path"

pip install requests
pip install mcproto
pip install aiohttp

# Make sure we clean up processes on exit
cleanup() {
  echo "Cleaning up processes..."
  pkill -f "ollama run qwen3:0.6b" || true
  pkill -f "python3 bot.py" || true
}

# Set up trap to call cleanup function when script exits
trap cleanup EXIT

# Start Ollama models in background
ollama run qwen3:0.6b &

# Start the Brook server
gnome-terminal -- bash -c "source ~/.profile && source ~/.bashrc && $(which bun || echo "$HOME/.bun/bin/bun") brook_server.ts"

# Start the bot
python3 bot.py
