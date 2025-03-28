#!/bin/bash

parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )

cd "$parent_path"

pip install requests
pip install mcproto
ollama run llama3.2:1b &
ollama run gemma2:2b &
python3 bot.py
