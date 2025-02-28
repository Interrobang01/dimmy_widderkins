#!/bin/bash
pip install requests
ollama run llama3.2:1b &
ollama run gemma2:2b &
python3 bot.py
