from util.data import *
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup

import re
import random
import time
import subprocess

github_API = GITHUBAPI

class Craw:

    @staticmethod
    def run(Year, Month):
        Craw.collect_cves(Year, Month)
        Craw.collect_commits(Year, Month)
        Craw.collect_repos(Year, Month)

    @staticmethod
    def collect_cves(Year, Month):
        YM = Year + '_' + Month
        cves_visited = 'cves/' + YM + '.log'

        headers = {
                    'User-Agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
                    'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Referer': 'https://www.mend.io/',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate'
                }

        if not exists_in_results(cves_visited):
            lprinty(os.path.join(RESULTSDIR, cves_visited), Colors.RED)

            url = "https://www.mend.io/vulnerability-database/full-listing/"+Year+"/"+Month 
            soup = BeautifulSoup(urlopen(Request(url,
                                headers=headers)).read(),
                                'html.parser')
        
            links = []
            try:
                max_pagenumber = int(soup.find_all("li", class_="vuln-pagination-item")[-2].text.strip())
            except Exception as e:
                lprinty("fial to get max page", Colors.YELLOW)
                max_pagenumber = 1

            for link in soup.find_all("a", href=re.compile("^/vulnerability-database/CVE")):
                href = link.get("href")
                links.append(href)
            if max_pagenumber > 1:
                for i in range(2,max_pagenumber+1):

                    url = "https://www.mend.io/vulnerability-database/full-listing/"+Year+"/"+ Month + '/'+str(i)
                    soup = BeautifulSoup(urlopen(Request(url,
                                headers=headers)).read(),
                                'html.parser')
                    for link in soup.find_all("a", href=re.compile("^/vulnerability-database/CVE")):
                        href = link.get("href")
                        links.append(href)

            for link in links:
                store_append_str(cves_visited, link)
        
    #------------------------------------------------------------------------------------------------------------------------            
        mend_information_path = 'mendInfo/' + YM + '.jsonl'
        
        content = load_lines(cves_visited)
        prefix = 'https://www.mend.io'

        max_num = 1  

        already_query_qid = 0
        if exists_in_results(mend_information_path):
            queried = load_lines(mend_information_path)
            already_query_qid = json.loads(queried[-1])["q_id"] if len(queried) != 0 else 0
            print(f'already query {already_query_qid}')

        for i in range(len(content)):
            try:
                time.sleep(random.uniform(0.1, 0.2))
                one_res = {"q_id":i ,"cve_id": content[i].strip().split('/')[-1], "language": 'NONE', "date": 'NONE', "resources": [], "CWEs": [] ,"cvss": None, "description":None, "AV":None, "AC":None, "PR":None, "UI":None, "S":None, "C":None, "I":None, "A":None}
                if i + 1 <= already_query_qid:
                    continue

                fullweb_url = prefix + content[i].strip()
                lprinty(fullweb_url, Colors.YELLOW)
                soup = BeautifulSoup(urlopen(Request(fullweb_url,
                                headers=headers)).read(),
                                'html.parser')

                for tag in soup.find_all(["h4"]):
                    if tag.name == "h4":
                        if "Date:" in tag.text:
                            one_res["date"] = tag.text.strip().replace("Date:", "").strip()

                        if "Language:" in tag.text:
                            one_res["language"] = tag.text.strip().replace("Language:", "").strip()
                
                div = soup.find("div", class_="single-vuln-desc no-good-to-know")
                if div:
                    desc = div.find("p")
                    description = desc.text.strip()
                    one_res["description"] = description
                
                div = soup.find("div", class_="single-vuln-desc")
                if div:
                    desc = div.find("p")
                    description = desc.text.strip()
                    one_res["description"] = description


                reference_links = []
                for div in soup.find_all("div", class_="reference-row"):
                    for link in div.find_all("a", href=True):
                        reference_links.append(link["href"])
                one_res["resources"] =  reference_links

                severity_score = ""
                div = soup.find("div", class_="ranger-value")
                if div:
                    label = div.find("label")
                    if label:
                        severity_score = label.text.strip()
                one_res["cvss"] =  severity_score

                table = soup.find("table", class_="table table-report")
                if table:
                    for tr in table.find_all("tr"):
                        th = tr.find('th').text.strip()
                        td = tr.find('td').text.strip()
                        if "Attack Vector" in th:
                            one_res["AV"] = td
                        elif "Attack Complexity" in th:
                            one_res["AC"] = td
                        elif "Privileges Required" in th:
                            one_res["PR"] = td
                        elif "User Interaction" in th:
                            one_res["UI"] = td
                        elif "Scope" in th:
                            one_res["S"] = td
                        elif "Confidentiality" in th:
                            one_res["C"] = td
                        elif "Integrity" in th:
                            one_res["I"] = td
                        elif "Availability" in th:
                            one_res["A"] = td

                if div:
                    label = div.find("label")
                    if label:
                        severity_score = label.text.strip()
                one_res["cvss"] =  severity_score

                cwe_numbers = []
                for div in soup.find_all("div", class_="light-box"):
                    for link in div.find_all("a", href=True):
                        if "CWE" in link.text:
                            cwe_numbers.append( link.text)
                one_res["CWEs"] =  cwe_numbers

                if (one_res["cve_id"] is not None) and (one_res["resources"] != []) and (one_res["CWEs"] != []) and (one_res["cvss"] is not None):
                    print("correct! all info is done for case", content[i])
                    store_append_json(mend_information_path, one_res)
                else:
                    if one_res["resources"] == []:
                        print('no source ,therefore give it up ',content[i])
                    else:
                        print("Wrong! At least one item in one_res is empty, see case ",content[i])
            except Exception as e:
                print(e)

    @staticmethod
    def collect_commits(Year, Month):
        YM = Year+'_'+Month
        mendio_info_path = 'mendInfo/' + YM + '.jsonl'
        res_path = 'mendInfoCommit/' + YM + '.jsonl'

        if not exists_in_results(mendio_info_path):
            critical(f'do not find {os.path.join(RESULTSDIR ,mendio_info_path)}, please run collect_cves first.')
            return

        
        with open(os.path.join(RESULTSDIR, mendio_info_path), "r", encoding="utf-8") as f:
            for line in f:
                mdic = json.loads(line)
                for res in mdic['resources']:
                    if "commit" in res and "github" in res:
                        query = res.replace('/commit/', '/commits/').replace('https://github.com/', 'https://api.github.com/repos/')
                        print(query)
                        # exit(0)
                        try:
                            output = bytes.decode(subprocess.check_output(["curl", "--request", "GET" ,"-H", f"Authorization: Bearer {github_API}", "-H", "X-GitHub-Api-Version: 2022-11-28", "-u", "KEY:", query]))
                            data = json.loads(output)
                        except Exception as e:
                            print(e)
                            continue
                        if 'url' in data and 'html_url' in data and 'commit' in data and 'files' in data:    
                            mdic['commit'] = {
                                'url': data['url'],
                                'html_url': data['html_url'],
                                'message': data['commit']['message'], 
                                'files': data['files'],
                                'commit_id': data['sha'],
                                'commit_date': data['commit']['committer']['date']
                            }
                        else:
                            mdic['commit'] = 'NONE'

                store_append_json(res_path, mdic)
                time.sleep(0.1)
        
    @staticmethod
    def collect_repos(Year, Month):
        mdic_path = 'mendInfoCommit/' + str(Year) + '_' + str(Month) + '.jsonl'

        if not exists_in_results(mdic_path):
            critical(f'do not find {os.path.join(RESULTSDIR ,mdic_path)}, please run collect_commits first.')
            return

        local_repos_path = os.path.join(RESULTSDIR, f'repos/{Year}_{Month}_repos')
        if not os.path.exists(local_repos_path):
            os.makedirs(local_repos_path)

        with open(os.path.join(RESULTSDIR, mdic_path), 'r') as f:
            for line in f:
                mdic = json.loads(line)

                url = mdic['commit']['url']
                repos_path = os.path.join(local_repos_path, f"{mdic['cve_id']}")
                if not os.path.exists(repos_path):
                    os.makedirs(repos_path)

                download_url = 'https://github.com/' + url.partition('/repos/')[2].partition('/commits/')[0] + '.git'
                repos_path = os.path.join(repos_path, url.partition('/repos/')[2].partition('/commits/')[0].replace('/','_'))

                lprinty(download_url + '\n' + repos_path, Colors.YELLOW)
                import git
                git.Repo.clone_from(download_url, repos_path)
                time.sleep(0.3)  
        
    @staticmethod
    def get_repos_via_mdic(Year, Month, mdic):
        url = mdic['commit']['url']
        local_repos_path = os.path.join(RESULTSDIR, f'repos/{Year}_{Month}_repos')
        if not os.path.exists(local_repos_path):
            os.makedirs(local_repos_path)
        repos_path = os.path.join(local_repos_path, f"{mdic['cve_id']}")
        if not os.path.exists(repos_path):
            os.makedirs(repos_path)

        download_url = 'https://github.com/' + url.partition('/repos/')[2].partition('/commits/')[0] + '.git'
        repos_path = os.path.join(repos_path, url.partition('/repos/')[2].partition('/commits/')[0].replace('/','_'))

        lprinty(download_url + '\n' + repos_path, Colors.YELLOW)
        import git
        git.Repo.clone_from(download_url, repos_path)



if __name__ == '__main__':
    Llogy.set_leve(LogLeve.CRITICAL)

    print(WORKDIR)
    print(RESULTSDIR)
    
    years = ['2025']
    months = ['5']
    for y in years:
        for m in months:
            # Craw.collect_cves(y, m)
            # Craw.collect_commits(y, m)
            Craw.collect_repos(y, m)