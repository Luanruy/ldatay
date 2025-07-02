from util.data import *

import sys
import os
sys.path.append(os.path.join(WORKDIR))
sys.path.append(os.path.join(WORKDIR, 'src/'))
sys.path.append(os.path.join(WORKDIR, 'util/'))

from src.craw import Craw
from src.staticAnalysis import PyhtonAnalysis
from util.llogy import *

from src.staticAnalysis import *

YEARS = ['2024', '2025']
MONTH = [f'{i+1}' for i in range(12)]

for y in YEARS:
    for m in MONTH:
        Craw.collect_cves(y, m)
        Craw.collect_commits(y, m)
        Craw.collect_repos(y, m)

        with open(os.path.join(RESULTSDIR, f'mendInfoCommit/{y}_{m}.jsonl'), 'r') as f:
            for line in f:
                mdic = json.loads(line)

                lprinty(mdic['cve_id'])

                # 判断项目使用的语言，可能不准确  后续更改  TODO
                file_language = set()
                if mdic['commit'] != 'NONE':
                    for file in mdic['commit']['files']:
                        file_language.add(file['filename'].split('.')[-1])
                
                if 'cpp' in file_language:
                    CppAnalysis(y, m, mdic)
                if 'go' in file_language:
                    GoAnalysis(y, m, mdic)
                if 'py' in file_language:
                    PyhtonAnalysis(y, m, mdic)
                
            
