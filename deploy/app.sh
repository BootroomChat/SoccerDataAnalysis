#!/bin/sh -l
pip3 install -r /bootroomchat/soccerdataanalysis/requirements.txt
pip3 install --no-cache-dir -r /bootroomchat/soccerdataanalysis/big-requirements.txt
uvicorn /bootroomchat/soccerdataanalysis/webapp/main:app --reload --port 8811