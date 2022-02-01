from importlib.abc import Loader
from  yaml  import load, safe_load
from os import path,getcwd
from pathlib import Path

curdir= path.dirname(__file__)
conf_file = path.join(curdir,'config.yml')
client_conf={}

with open(conf_file,'r') as conf:
    client_conf = safe_load(conf.read())

# import json 
# print(client_conf['clusters'][0]['hosts'])