import configparser
import functools
import os


@functools.lru_cache()
def default_config():
    conf = configparser.ConfigParser()
    root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    conf.read(root_path+'/config/brchat.conf')
    return conf
