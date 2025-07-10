from dealMdic import DealMdic
from git import Repo, GitCommandError
from util.data import *

import os

class PyhtonAnalysis(DealMdic):
    def __init__(self, y, m, mdic):
        super().__init__(y, m, mdic)
        self.analyz(self.get_function_at_line_ast_python)
        self.store_result()

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


class GoAnalysis(DealMdic):
    def __init__(self, y, m, mdic):
        super().__init__(y, m, mdic)
        self.analyz(self.get_function_at_line_go)
        self.store_result()

    def get_function_at_line_go(self, source, target_line):
        """
        Extract the complete Go function that contains the target line number.
        The returned function code includes line numbers.

        Args:
            source (str): The Go source code as a string.
            target_line (int): The line number to locate (1-based).

        Returns:
            tuple[str, str] or None: A (function_name, function_code_with_lineno) tuple if found, else None.
        """
        import re
        
        lines = source.splitlines()
        if target_line > len(lines) or target_line < 1:
            return None, None

        # Go function patterns
        func_pattern = r'^\s*func\s+(?:\([^)]*\)\s+)?(\w+)\s*\([^)]*\)(?:\s*[^{]*)?{'
        
        best_match = None
        best_start = -1
        
        for i, line in enumerate(lines):
            match = re.match(func_pattern, line)
            if match:
                func_name = match.group(1)
                start_line = i + 1
                
                # Find the end of the function by counting braces
                brace_count = 0
                end_line = start_line
                found_opening = False
                
                for j in range(i, len(lines)):
                    for char in lines[j]:
                        if char == '{':
                            brace_count += 1
                            found_opening = True
                        elif char == '}':
                            brace_count -= 1
                            if found_opening and brace_count == 0:
                                end_line = j + 1
                                break
                    if found_opening and brace_count == 0:
                        break
                
                # Check if target line is within this function
                if start_line <= target_line <= end_line:
                    if start_line > best_start:
                        best_match = {
                            'name': func_name,
                            'start': start_line,
                            'end': end_line
                        }
                        best_start = start_line
        
        if not best_match:
            return None, None
        
        start = best_match['start'] - 1  # 0-based index
        end = best_match['end']          # inclusive in splitlines
        
        # Add line numbers
        func_lines = [
            f"{i + 1:>5}: {line}" for i, line in enumerate(lines[start:end], start=start)
        ]
        func_code = '\n'.join(func_lines)
        
        return best_match['name'], func_code


class CppAnalysis(DealMdic):
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
                    fun_name, func = self.get_function_at_line_cpp(source_bef, cg['line_number'])
                    if fun_name != None:
                        f_bef[fun_name] = func
                if cg['type'] == 'added':
                    lprinty(cg['line_number'])
                    fun_name, func = self.get_function_at_line_cpp(source_now, cg['line_number'])
                    if fun_name != None:
                        f_now[fun_name] = func
            
            print(f_bef)
            print(f_now)

    def get_function_at_line_cpp(self, source, target_line):
        """
        Extract the complete C/C++ function that contains the target line number.

        Args:
            source (str): The C/C++ source code as a string.
            target_line (int): The line number to locate (1-based).

        Returns:
            tuple[str, str] or None: A (function_name, function_code) tuple if found, else None.
        """
        import re
        
        lines = source.splitlines()
        if target_line > len(lines) or target_line < 1:
            return None, None

        # C/C++ function patterns
        # Match various function definitions including:
        # - return_type function_name(params) {
        # - Class::method_name(params) {
        # - template functions, etc.
        func_patterns = [
            r'^\s*(?:(?:inline|static|virtual|explicit|template\s*<[^>]*>)\s+)*(?:\w+(?:\s*\*|\s*&)?(?:\s*::\s*\w+)*\s+)?(\w+(?:::\w+)?)\s*\([^)]*\)(?:\s*const)?\s*(?:override)?\s*{',
            r'^\s*(?:(?:inline|static|virtual|explicit)\s+)*(?:\w+(?:\s*\*|\s*&)?(?:\s*::\s*\w+)*\s+)?(\w+)\s*\([^)]*\)(?:\s*const)?\s*(?:override)?\s*{'
        ]
        
        best_match = None
        best_start = -1
        
        for i, line in enumerate(lines):
            for pattern in func_patterns:
                match = re.match(pattern, line)
                if match:
                    func_name = match.group(1)
                    start_line = i + 1
                    
                    # Find the end of the function by counting braces
                    brace_count = 0
                    end_line = start_line
                    found_opening = False
                    
                    for j in range(i, len(lines)):
                        for char in lines[j]:
                            if char == '{':
                                brace_count += 1
                                found_opening = True
                            elif char == '}':
                                brace_count -= 1
                                if found_opening and brace_count == 0:
                                    end_line = j + 1
                                    break
                        if found_opening and brace_count == 0:
                            break
                    
                    # Check if target line is within this function
                    if start_line <= target_line <= end_line:
                        if start_line > best_start:
                            best_match = {
                                'name': func_name,
                                'start': start_line,
                                'end': end_line
                            }
                            best_start = start_line
                    break
        
        if not best_match:
            return None, None
        
        func_lines = lines[best_match['start']-1:best_match['end']]
        func_code = '\n'.join(func_lines)
        
        return best_match['name'], func_code



if __name__ == '__main__':
    pa = PyhtonAnalysis(2025, 5, "zzz")