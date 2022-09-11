import os
from typing import Union
import oss2
from fastapi import FastAPI
from starlette.responses import FileResponse
from config.config import default_config

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

