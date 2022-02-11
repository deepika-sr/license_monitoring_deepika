from importlib.abc import Loader
from  yaml  import load, safe_load
from os import path,getcwd
from pathlib import Path

curdir= path.dirname(__file__)
conf_file = path.join(curdir,'config.yml')


# Every Time read from file.s
def get_client_config():
    with open(conf_file,'r') as conf:
        client_conf = safe_load(conf.read())
        return client_conf