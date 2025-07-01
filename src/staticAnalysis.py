from dealMdic import DealMdic
from git import Repo, GitCommandError
from util.data import *

import os

class PyhtonAnalysis(DealMdic):
    def __init__(self, y, m, mdic):
        super().__init__(y, m, mdic)
        self.analyz()

    def analyz(self):
        for pf in self.patch_files:
            changes = self.get_changed_statements(pf[0])
            source_bef = self.get_code_at_commit(self.repos_dir, self.get_previous_commit(pf[1]), pf[1])
            source_now = self.get_code_at_commit(self.repos_dir, self.commit_id, pf[1])
            f_bef = dict()
            f_now = dict()
            for cg in changes:

                if cg['type'] == 'removed':
                    fun_name, func = self.get_function_at_line_ast_python(source_bef, cg['line_number'])
                    if fun_name != None:
                        f_bef[fun_name] = func
                if cg['type'] == 'added':
                    lprinty(cg['line_number'])
                    fun_name, func = self.get_function_at_line_ast_python(source_now, cg['line_number'])
                    if fun_name != None:
                        f_now[fun_name] = func
            
            print(f_bef)
            print(f_now)

                
            
            
    def get_function_at_line_ast_python(self, source, target_line):
        """
        Use the ast module to extract the complete function (with decorators and class context)
        that contains the target line number.

        Args:
            source (str): The source code as a string.
            target_line (int): The line number to locate (1-based).

        Returns:
            tuple[str, str] or None: A (function_name, function_code) tuple if found, else None.
        """
        import ast
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return None

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
        start = finder.best_match['start_line'] - 1
        end = finder.best_match['end_line']
        lines = source.splitlines()

        func_code = '\n'.join(lines[start:end])
        func_name = node.name

        if finder.best_match['class_name']:
            func_name = f"{finder.best_match['class_name']}.{func_name}"
            func_code = f"# Class: {finder.best_match['class_name']}\n{func_code}"
        
        return func_name, func_code



    

        


    def test(self):
        pass



if __name__ == '__main__':
    pa = PyhtonAnalysis(2025, 5, "zzz")