from src.craw import Craw
from util.data import *
# Craw.collect_cves(2025, 5)
# Craw.collect_commits(2025, 5)

sf = set()

# with open(f"{RESULTSDIR}/mendInfoCommit/2025_5.jsonl", 'r') as f:
#     for line in f:
#         mdic = json.loads(line)
#         for file in mdic['commit']['files']:
#             filename = file['filename']

#             t = filename.split('.')[-1]
#             sf.add(t)
#             if t == 'c':
#                 lprinty(f'c:  {mdic['q_id']}    {mdic['cve_id']}')
#             if t == 'cpp':
#                 lprinty(f'cpp:  {mdic['q_id']}  {mdic['cve_id']}')
        
# print(sf)


"""

lprinty:  
c:  16    CVE-2025-40909
at /Users/launruy/Mythings/Qianxin/ldatay/test2.py: line 17
lprinty:  
c:  54    CVE-2025-27151
at /Users/launruy/Mythings/Qianxin/ldatay/test2.py: line 17
lprinty:  
cpp:  79  CVE-2025-48057
at /Users/launruy/Mythings/Qianxin/ldatay/test2.py: line 19
lprinty:  
cpp:  79  CVE-2025-48057
at /Users/launruy/Mythings/Qianxin/ldatay/test2.py: line 19
lprinty:  
c:  141    CVE-2025-4575
at /Users/launruy/Mythings/Qianxin/ldatay/test2.py: line 17
lprinty:  
c:  156    CVE-2024-23337
at /Users/launruy/Mythings/Qianxin/ldatay/test2.py: line 17
lprinty:  
c:  156    CVE-2024-23337

"""
mdic = get_mdic(2025, 5, 'CVE-2024-23337')
Craw.get_repos_via_mdic(2025, 5, mdic)
for file in mdic['commit']['files']:
    lprinty(file['filename'])