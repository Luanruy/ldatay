from git import Repo, GitCommandError
from util.data import *

import shutil
import re

class DealMdic:

    def __init__(self, y, m, mdic):
        self.YM = str(y) + '_' + str(m)
        self.mdic = mdic

        self.cve_id = self.mdic['cve_id']
        self.repos_name = self._get_repos_name(self.mdic)
        self.repos_dir = os.path.join(RESULTSDIR, f'repos/{self.YM}_repos', self.mdic['cve_id'], self.repos_name)
        self.patch_files = self._get_patch_files(self.mdic)
        self.commit_id = self.mdic['commit']['commit_id']

        self.result = mdic
        self.result['analysis'] = {}
        self.result.pop('q_id')

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
        """
        获取某个commit中指定文件的代码内容
        
        Args:
            repos_dir (str): 仓库目录路径
            commit (str): commit哈希值
            filename (str): 文件名
            
        Returns:
            str or None: 文件内容，如果文件不存在则返回None
        """
        if commit is None:
            return None
            
        repo = Repo(repos_dir)
        try:
            return repo.git.show(f"{commit}:{filename}")
        except GitCommandError as e:
            # 如果文件在该commit中不存在，返回None
            if "exists on disk, but not in" in e.stderr or "does not exist" in e.stderr or "path does not exist" in e.stderr:
                return None
            # 其他Git错误仍然抛出异常
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
        返回修改filename文件的前一个commit哈希值
        
        使用git log来找到在当前commit之前最近一次修改该文件的commit
        
        Args:
            filename (str): 文件名
            
        Returns:
            str or None: 前一个修改该文件的commit哈希值，如果不存在则返回None
        """
        repo = Repo(self.repos_dir)
        
        try:
            # 使用git log --follow来追踪文件历史，包括重命名
            # -n 2 获取最近的2个commit（第一个是当前commit，第二个是我们要的前一个）
            # --pretty=format:%H 只输出commit哈希值
            log_output = repo.git.log(
                '--follow', 
                '--pretty=format:%H', 
                '-n', '2',
                self.commit_id,
                '--',
                filename
            )
            
            commits = log_output.strip().split('\n')
            
            # 如果只有一个commit，说明这是第一次引入该文件
            if len(commits) <= 1:
                return None
                
            # 第一个是当前commit，第二个是前一个修改该文件的commit
            if len(commits) >= 2 and commits[1].strip():
                return commits[1].strip()
                
            return None
            
        except GitCommandError as e:
            # 如果文件不存在或其他git错误
            print(f"Warning: Could not get previous commit for {filename}: {e}")
            return None  
        

    def analyz(self, get_function_at_line):
        for pf in self.patch_files:
            changes = self.get_changed_statements(pf[0])
            precommit = self.get_previous_commit(pf[1])
            source_bef = self.get_code_at_commit(self.repos_dir, self.get_previous_commit(pf[1]), pf[1]) if precommit else None
            source_now = self.get_code_at_commit(self.repos_dir, self.commit_id, pf[1])
            f_bef = dict()
            f_now = dict()
            for cg in changes:

                if cg['type'] == 'removed':
                    fun_name, func = get_function_at_line(source_bef, cg['line_number'])
                    if fun_name != None:
                        if fun_name not in f_bef:
                            f_bef[fun_name] = {}
                            f_bef[fun_name]['code'] = func
                            f_bef[fun_name]['removed'] = list()
                        f_bef[fun_name]['removed'].append(f"-    {cg['line_number']}:{cg['content']}")
                    else:
                        pass   #TODO  同一个文件内可能有不在函数内的删减，这种情况应该定位某些行数保留下来

                if cg['type'] == 'added':
                    fun_name, func = get_function_at_line(source_now, cg['line_number'])
                    if fun_name != None:
                        if fun_name not in f_now:
                            f_now[fun_name] = {}
                            f_now[fun_name]['code'] = func
                            f_now[fun_name]['added'] = list()
                        f_now[fun_name]['added'].append(f"+    {cg['line_number']}:{cg['content']}")
                    else:
                        pass    #TODO  同一个文件内可能有不在函数内的删减，这种情况应该定位某些行数保留下来
           
            names = set()
            for _ in f_bef:
                names.add(_)
            for _ in f_now:
                names.add(_)

            for name in names:
                if pf[1] not in self.result['analysis']:
                    self.result['analysis'][pf[1]] = {}
                    
                if name not in self.result['analysis'][pf[1]]:
                    self.result['analysis'][pf[1]][name] = {}

                self.result['analysis'][pf[1]][name]['before'] = f_bef[name] if name in f_bef else None
                self.result['analysis'][pf[1]][name]['now'] = f_now[name] if name in f_now else None
                self.result['analysis'][pf[1]][name]['callers'] = None   #TODO  获取某个项目某个文件中某个函数的所有caller
                self.result['analysis'][pf[1]][name]['callees'] = None   #TODO  获取某个项目某个文件中某个函数的所有callee

            if len(names) == 0:
                # TODO patch修改的内容完全不涉及函数，直接将patch保留，后续可以扩充为保留某一行的前后多少行  
                # lprinty(pf[0])
                if pf[1] not in self.result['analysis']:
                    self.result['analysis'][pf[1]] = {}
                self.result['analysis'][pf[1]]['patch'] = pf[0]


    def store_result(self):
        lprinty(f'{self.cve_id} analysis compelete, storing.....')
        if not os.path.exists(f'{RESULTSDIR}/results/'):
            os.makedirs(f'{RESULTSDIR}/results/')

        with open(f'{RESULTSDIR}/results/{self.cve_id}.json', 'w') as f:
            json.dump(self.result, f, ensure_ascii=False, indent=4)   

if __name__ == "__main__":
    ef = DealMdic(2025, 5)
