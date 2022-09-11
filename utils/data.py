import functools
import os
from sys import platform
import pandas as pd


@functools.lru_cache()
def load_client_info():
    root_path = os.path.abspath(os.path.join(os.getcwd(), "../.."))
    if platform == "win32":
        path = root_path + 'data/sales.csv'
    else:
        path = root_path+'bootroomchat/data/sales.csv'
    df = pd.read_csv(path)
    return df


def save_client_info(df: pd.DataFrame):
    root_path = os.path.abspath(os.path.join(os.getcwd(), "../.."))
    if platform == "win32":
        path = root_path + 'data/sales.csv'
    else:
        path = root_path+'bootroomchat/data/sales.csv'
    df.to_csv(path, index=False)
