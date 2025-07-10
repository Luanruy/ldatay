from util.data import *

import sys
import os
sys.path.append(os.path.join(WORKDIR))
sys.path.append(os.path.join(WORKDIR, 'src/'))
sys.path.append(os.path.join(WORKDIR, 'util/'))

from src.craw import Craw
from util.llogy import *

from src.staticAnalysis import *

y = '2025'
m = '5'

# cve_id = 'CVE-2025-48948' # go 
# cve_id = 'CVE-2018-25111' # py
cve_id = 'CVE-2025-48883' # php
cve_id = 'CVE-2024-23337' #cpp


mdic = None
with open(os.path.join(RESULTSDIR, f'mendInfoCommit/{y}_{m}.jsonl'), 'r') as f:
    for line in f:
        temp_mdic = json.loads(line)
        if temp_mdic['cve_id'] == cve_id:
            mdic = temp_mdic
            lprinty(f"找到目标CVE: {mdic['cve_id']}")
            break

if mdic is None:
    print(f"错误：未找到CVE ID {cve_id}")
    exit(1)

file_language = set()
if mdic['commit'] != 'NONE':
    for file in mdic['commit']['files']:
        file_language.add(file['filename'].split('.')[-1])

# lprinty(mdic['commit']['files'][0]['patch'])
# exit(0)


if 'cpp' in file_language or 'c' in file_language:
    CppAnalysis(y, m, mdic)
elif 'go' in file_language:
    GoAnalysis(y, m, mdic)
elif 'php' in file_language:
    print(mdic['language'])
    PhpAnalysis(y, m, mdic)
elif 'py' in file_language:
    PyhtonAnalysis(y, m, mdic)
    
