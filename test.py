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
cve_id = 'CVE-2018-25111' # py


with open(os.path.join(RESULTSDIR, f'mendInfoCommit/{y}_{m}.jsonl'), 'r') as f:
    for line in f:
        mdic = json.loads(line)
        lprinty(mdic['cve_id']) 
        if mdic['cve_id'] == cve_id:
            break

file_language = set()
if mdic['commit'] != 'NONE':
    for file in mdic['commit']['files']:
        file_language.add(file['filename'].split('.')[-1])


if 'cpp' in file_language:
    CppAnalysis(y, m, mdic)
if 'go' in file_language:
    lprinty('gogogogogogogo')
    exit(0)
    GoAnalysis(y, m, mdic)
if 'py' in file_language:
    PyhtonAnalysis(y, m, mdic)
    
