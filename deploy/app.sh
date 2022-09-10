#!/bin/sh -l
BUILD_ID=DONTKILLME
pip3 install -r /bootroomchat/soccerdataanalysis/requirements.txt
ps -ef |grep send_report |awk '{print $2}'|xargs kill -9
cd  /bootroomchat/soccerdataanalysis
nohup python3 -m batch.send_report > test.out 2>&1 &
ps -ef |grep uvicorn |awk '{print $2}'|xargs kill -9
nohup uvicorn webapp.main:app --port 8811 --host 0.0.0.0 > test.out 2>&1 &
exit