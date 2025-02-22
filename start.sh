#!/bin/bash
pip install requests
ollama run llama3.2:1b &
python3 bot.py
