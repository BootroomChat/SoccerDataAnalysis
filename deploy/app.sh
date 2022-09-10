#!/bin/sh -l
BUILD_ID=DONTKILLME
pip3 install -r /bootroomchat/soccerdataanalysis/requirements.txt
ps -ef |grep send_report |awk '{print $2}'|xargs kill -9
cd  /bootroomchat/soccerdataanalysis && python3 -m batch.send_report
cd  /bootroomchat/soccerdataanalysis/webapp
ps -ef |grep uvicorn |awk '{print $2}'|xargs kill -9
nohup uvicorn main:app --port 8811 --host 0.0.0.0 &
exit