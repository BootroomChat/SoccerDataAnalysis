#!/bin/sh -l
#pip3 install -r /bootroomchat/soccerdataanalysis/requirements.txt
#pip3 install --no-cache-dir -r /bootroomchat/soccerdataanalysis/big-requirements.txt
cd  /bootroomchat/soccerdataanalysis/webapp
BUILD_ID=DONTKILLME
ps -ef |grep uvicorn |awk '{print $2}'|xargs kill -9
nohup uvicorn main:app --port 8811 --host 0.0.0.0 &
exit