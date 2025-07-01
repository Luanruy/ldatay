from util.data import *

import sys
import os
sys.path.append(os.path.join(WORKDIR))
sys.path.append(os.path.join(WORKDIR, 'src/'))
sys.path.append(os.path.join(WORKDIR, 'util/'))

from src.craw import Craw
from src.staticAnalysis import PyhtonAnalysis


with open(os.path.join(RESULTSDIR, 'mendInfoCommit/2025_5.jsonl'), 'r') as f:
    for line in f:
        mdic = json.loads(line)
        break

pa = PyhtonAnalysis(2025, 5, mdic)


