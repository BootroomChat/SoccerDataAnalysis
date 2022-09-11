import os
from typing import Union
import oss2
from fastapi import FastAPI
from starlette.responses import FileResponse
from config.config import default_config
from utils.data import load_client_info, save_client_info

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


@app.get("/reports/get_report")
def get_report(match_date: str, team: str):
    config = default_config()
    aliyun_access_key = config.get("aliyun", "aliyun_access_key")
    aliyun_secret = config.get("aliyun", "aliyun_secret")
    auth = oss2.Auth(aliyun_access_key, aliyun_secret)
    bucket = 'soccer-matches-hk'
    bucket = oss2.Bucket(auth, 'http://oss-cn-hongkong.aliyuncs.com', bucket)
    this_report_lst = list()
    for file_path in oss2.ObjectIterator(bucket, prefix='reports/'):
        this_report_lst.append(file_path.key)
    for each_report in this_report_lst:
        if team in each_report and match_date in each_report:
            local_path = each_report.replace('reports', '')
            root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            local_path = root_path + local_path + '.pdf'
            if not os.path.exists(local_path):
                bucket.get_object_to_file(each_report, local_path)
            return FileResponse(local_path, filename='report.pdf')
    return "No match report!"


@app.post("/data/add_client")
def add_client(client_name: str, sales: str, email: str, season: str, league: str, team: str, level: str,
               trial: bool = True,
               member_ship: bool = False):
    info = load_client_info()

    new_id = info['ClientID'].max() + 1
    new_line = {'ClientID': new_id, 'ClientName': client_name, 'Sales': sales, 'Email': email, 'Season': season,
                'League': league, 'Team': team, 'Level': level, 'Trial': trial, 'Membership': member_ship,
                'ReportSent': 0}
    info = info.append(new_line, ignore_index=True)
    save_client_info(info)


@app.post("/data/delete_client")
def delete_client(client_id: int):
    info = load_client_info()
    info = info.drop(info[info['ClientID'] == client_id].index)
    save_client_info(info)
