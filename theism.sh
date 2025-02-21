#!/bin/bash
# hii i addeds some AI stuff and some dependencies so this will like install them and run the models if you have everythig installed
pip install requests
ollama run llama3.2:1b &
python3 bot.py
