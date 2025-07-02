from git import Repo, GitCommandError
from util.data import *

import shutil
import re

class DealMdic:

    def __init__(self, y, m, mdic):
        self.YM = str(y) + '_' + str(m)
        data = [json.loads(_) for _ in load_lines(f'mendInfoCommit/{self.YM}.jsonl')]
        self.mdic = data[0]

        self.cve_id = self.mdic['cve_id']
        self.repos_name = self._get_repos_name(self.mdic)
        self.repos_dir = os.path.join(RESULTSDIR, f'repos/{self.YM}_repos', self.mdic['cve_id'], self.repos_name)
        self.patch_files = self._get_patch_files(self.mdic)
        self.commit_id = self.mdic['commit']['commit_id']

        self.result = {}
        self.result['cve_id'] = self.cve_id
        self.result['cve description'] = self.mdic['description']
        self.result['commit message'] = self.mdic['commit']['message']

    def _get_patch_files(self, mdic):
        patch_files = []
        for file in mdic['commit']['files']:
            patch_files.append((file['patch'], file['filename']))
        return patch_files

    def _get_repos_name(self, mdic):
        for resour in mdic['resources']:
            resour : str
            if '//github.com/' in resour and '/commit/' in resour:
                return resour.split('.com/')[1].split('/commit/')[0].replace('/', '_')
        return None
    
    @staticmethod
    def get_code_at_commit(repos_dir, commit, filename):
        repo = Repo(repos_dir)
        try:
            return repo.git.show(f"{commit}:{filename}")
        except GitCommandError as e:
            raise RuntimeError(f"Git error: {e.stderr.strip()}") from e
    
    @staticmethod
    def mk_tmp_commit_repos(repo_path, commit_hash, language, cve_id):
        if language not in ['py', 'c', 'cpp', 'go', 'php']:
            critical(f'not support {language} yet')
            return
        
        temp_dir = os.path.join(RESULTSDIR, 'tmp', cve_id)
        os.makedirs(temp_dir, exist_ok=True)
        repo = Repo(repo_path)
        commit = repo.commit(commit_hash)

        for item in commit.tree.traverse():
            if item.type == "blob":  # 仅处理文件（而非目录）
                file_path = item.path
                if file_path.endswith('.' + language):
                    try:
                        file_content = repo.git.show(f"{commit_hash}:{file_path}")
                        full_path = os.path.join(temp_dir, file_path)
                        os.makedirs(os.path.dirname(full_path), exist_ok=True)
                        with open(full_path, "w", encoding="utf-8") as f:
                            f.write(file_content)
                    except Exception as e:
                        print(f"Error reading {file_path}: {e}")
        
        return temp_dir

    @staticmethod
    def rm_tmp_commit_repos(tmp_dir):
        shutil.rmtree(tmp_dir)

    @staticmethod
    def get_changed_statements(patch_text):
        """
        :return: {
                    'type': 'removed or add',
                    'block': current_block,
                    'line_number': old_line_num,
                    'content': line[1:].rstrip()
                }
        """
        changes = []
        current_block = None
        
        block_header_pattern = re.compile(r'^@@ -(\d+),(\d+) \+(\d+),(\d+) @@')
        
        lines = patch_text.split('\n')
        old_line_num = None
        new_line_num = None
        
        for line in lines:
            if line.startswith('@@'):
                match = block_header_pattern.match(line)
                if match:
                    old_start = int(match.group(1))
                    new_start = int(match.group(3))
                    
                    old_line_num = old_start
                    new_line_num = new_start
                    current_block = line
                continue
            
            if old_line_num is not None and new_line_num is not None:
                if line.startswith(' '):
                    old_line_num += 1
                    new_line_num += 1
                elif line.startswith('-'):
                    changes.append({
                        'type': 'removed',
                        'block': current_block,
                        'line_number': old_line_num,
                        'content': line[1:].rstrip()
                    })
                    old_line_num += 1
                elif line.startswith('+'):
                    changes.append({
                        'type': 'added',
                        'block': current_block,
                        'line_number': new_line_num,
                        'content': line[1:].rstrip()
                    })
                    new_line_num += 1
        
        return changes

    def get_previous_commit(self, filename):
        """
        返回某个 commit 修改 filename 之前的 commit（即 filename 的上一个版本所在的 commit）。
        """
        repo = Repo(self.repos_dir)
        commit = repo.commit(self.commit_id)

        if len(commit.parents) > 1:
            for parent in commit.parents:
                try:
                    diff = commit.diff(parent, paths=filename)
                    if diff: 
                        return parent.hexsha
                except GitCommandError:
                    continue
            return None  

        if commit.parents:
            return commit.parents[0].hexsha

        return None  

    def store_result(self):
        if not os.path.exists(f'{RESULTSDIR}/results/'):
            os.makedirs(f'{RESULTSDIR}/results/')

        with open(f'{RESULTSDIR}/results/{self.cve_id}.json', 'w') as f:
            json.dump(self.result, f, ensure_ascii=False, indent=4)   

if __name__ == "__main__":
    ef = DealMdic(2025, 5)
