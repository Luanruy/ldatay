from util.llogy import *

import os
import json

WORKDIR = os.path.dirname(os.path.dirname(__file__))
RESULTSDIR = os.path.join(WORKDIR, 'outputs')

with open(os.path.join(WORKDIR, 'config.json'), 'r') as f:
    GITHUBAPI = json.load(f)['git_api'] 

def exists_in_results(result_name):
    return os.path.exists(os.path.join(RESULTSDIR, result_name))

def store_data_json(result_name, data):
    file_path  = os.path.join(RESULTSDIR, result_name)
    file_dir = os.path.dirname(file_path)
    if not os.path.exists(file_dir):
        os.mkdir(file_dir)
    with open(file_path, 'w') as f:
        json.dump(data, f)
    
def store_append_json(result_name, data):
    file_path  = os.path.join(RESULTSDIR, result_name)
    file_dir = os.path.dirname(file_path)
    if not os.path.exists(file_dir):
        os.mkdir(file_dir)
    with open(file_path, 'a') as f:
        jsonobj = json.dumps(data, ensure_ascii=False)
        f.write(jsonobj + '\n')

def store_json_lines(result_name, data):
    file_path = os.path.join(RESULTSDIR, result_name)
    file_dir = os.path.dirname(file_path)
    if not os.path.exists(file_dir):
        os.mkdir(file_dir)
    with open(file_path, 'w') as f:
        for d in data:
            f.write(json.dumps(d, ensure_ascii=False) + '\n')

def store_append_str(result_name, s):
    file_path  = os.path.join(RESULTSDIR, result_name)
    file_dir = os.path.dirname(file_path)
    if not os.path.exists(file_dir):
        os.mkdir(file_dir)
    with open(file_path, 'a') as f:
        f.write(s + '\n')
        
def load_data_json(result_name):
    file_path  = os.path.join(RESULTSDIR, result_name)
    if not exists_in_results(result_name):
        lprinty_line(f"not exist file: {file_path}", Colors.YELLOW)
        exit(0)
    with open(file_path, 'r') as f: 
        data = json.load(f)
    return data

def load_lines(result_name):
    file_path  = os.path.join(RESULTSDIR, result_name)
    if not exists_in_results(result_name):
        lprinty_line(f"not exist file: {file_path}", Colors.CYAN)
        exit(0)
    with open(file_path, 'r') as f:
        content = f.readlines()
    return content
