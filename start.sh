#!/bin/bash
pip install requests
pip install mcproto
ollama run llama3.2:1b &
ollama run gemma2:2b &
python3 bot.py
