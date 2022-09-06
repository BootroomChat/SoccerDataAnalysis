import soccerdata as sd

if __name__ == '__main__':
    ws = sd.WhoScored(leagues="ENG-Premier League", seasons='2021',proxy='tor')
    print(ws.__doc__)
    epl_schedule = ws.read_schedule()
    epl_schedule.head()