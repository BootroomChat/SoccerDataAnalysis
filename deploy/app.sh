#!/bin/sh -l
BUILD_ID=DONTKILLME
nohup pip3.8 install -r /bootroomchat/soccerdataanalysis/requirements.txt > test.out 2>&1 &
ps -ef |grep send_report |awk '{print $2}'|xargs kill -9
cd  /bootroomchat/soccerdataanalysis
nohup python3.8 -m batch.send_report > test.out 2>&1 &
ps -ef |grep uvicorn |awk '{print $2}'|xargs kill -9
nohup python3.8 -m uvicorn webapp.main:app --port 8811 --host 0.0.0.0 > test.out 2>&1 &
crontab /bootroomchat/soccerdataanalysis/cron.d/batch.cron
exit