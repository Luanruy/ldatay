from dealMdic import DealMdic
from git import Repo, GitCommandError
from util.data import *

import os

class PyhtonAnalysis(DealMdic):
    def __init__(self, y, m, mdic):
        super().__init__(y, m, mdic)
        self.analyz()
        self.store_result()

    def analyz(self):
        for pf in self.patch_files:
            changes = self.get_changed_statements(pf[0])
            source_bef = self.get_code_at_commit(self.repos_dir, self.get_previous_commit(pf[1]), pf[1])
            source_now = self.get_code_at_commit(self.repos_dir, self.commit_id, pf[1])
            f_bef = dict()
            f_now = dict()
            for cg in changes:

                if cg['type'] == 'removed':
                    lprinty(cg)
                    fun_name, func = self.get_function_at_line_ast_python(source_bef, cg['line_number'])
                    if fun_name != None:
                        if fun_name not in f_bef:
                            f_bef[fun_name] = {}
                            f_bef[fun_name]['code'] = func
                            f_bef[fun_name]['removed'] = list()
                        f_bef[fun_name]['removed'].append(f"-    {cg['line_number']}:{cg['content']}")
                    else:
                        pass   #TODO 同一个文件内可能有不在函数内的删减，这种情况应该定位某些行数保留下来

                if cg['type'] == 'added':
                    lprinty(cg)
                    fun_name, func = self.get_function_at_line_ast_python(source_now, cg['line_number'])
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
                if pf[1] not in self.result:
                    self.result[pf[1]] = {}
                    
                if name not in self.result[pf[1]]:
                    self.result[pf[1]][name] = {}

                self.result[pf[1]][name]['before'] = f_bef[name] if name in f_bef else None
                self.result[pf[1]][name]['now'] = f_now[name] if name in f_now else None
                self.result[pf[1]][name]['callers'] = None   #TODO  获取某个项目某个文件中某个函数的所有caller
                self.result[pf[1]][name]['callees'] = None   #TODO  获取某个项目某个文件中某个函数的所有callee

            if len(names) == 0:
                # TODO patch修改的内容完全不涉及函数，直接将patch保留，后续可以扩充为保留某一行的前后多少行  
                lprinty(pf[0])
                if pf[1] not in self.result:
                    self.result[pf[1]] = {}
                self.result[pf[1]]['patch'] = pf[0]

    def get_function_at_line_ast_python(self, source, target_line):
        """
        Use the ast module to extract the complete function (with decorators and class context)
        that contains the target line number. The returned function code includes line numbers.

        Args:
            source (str): The source code as a string.
            target_line (int): The line number to locate (1-based).

        Returns:
            tuple[str, str] or None: A (function_name, function_code_with_lineno) tuple if found, else None.
        """
        import ast
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return None, None

        class FunctionFinder(ast.NodeVisitor):
            def __init__(self):
                self.current_class = None
                self.best_match = None

            def visit_ClassDef(self, node):
                self.current_class = node.name
                self.generic_visit(node)
                self.current_class = None

            def visit_FunctionDef(self, node):
                self._process_function(node)
                self.generic_visit(node)

            def visit_AsyncFunctionDef(self, node):
                self._process_function(node)
                self.generic_visit(node)

            def _process_function(self, node):
                start_line = min(
                    [d.lineno for d in node.decorator_list] + [node.lineno]
                )
                end_line = getattr(node, 'end_lineno', None)
                if end_line is None:
                    end_line = max(
                        (child.lineno for child in ast.walk(node) if hasattr(child, 'lineno')),
                        default=node.lineno
                    )
                if start_line <= target_line <= end_line:
                    if (self.best_match is None or start_line > self.best_match['start_line']):
                        self.best_match = {
                            'node': node,
                            'start_line': start_line,
                            'end_line': end_line,
                            'class_name': self.current_class
                        }

        finder = FunctionFinder()
        finder.visit(tree)

        if not finder.best_match:
            return None, None

        node = finder.best_match['node']
        start = finder.best_match['start_line'] - 1  # 0-based index
        end = finder.best_match['end_line']          # inclusive in splitlines

        lines = source.splitlines()

        # Add line numbers
        func_lines = [
            f"{i + 1:>5}: {line}" for i, line in enumerate(lines[start:end], start=start)
        ]
        func_code = '\n'.join(func_lines)

        func_name = node.name
        if finder.best_match['class_name']:
            func_name = f"{finder.best_match['class_name']}.{func_name}"
            func_code = f"# Class: {finder.best_match['class_name']}\n{func_code}"

        return func_name, func_code

    

        


    def test(self):
        pass



if __name__ == '__main__':
    pa = PyhtonAnalysis(2025, 5, "zzz")