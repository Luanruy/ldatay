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
            prev_commit = self.get_previous_commit(pf[1])
            source_bef = self.get_code_at_commit(self.repos_dir, prev_commit, pf[1]) if prev_commit else None
            source_now = self.get_code_at_commit(self.repos_dir, self.commit_id, pf[1])
            
            f_bef = dict()
            f_now = dict()
            for cg in changes:

                if cg['type'] == 'removed' and source_bef is not None:
                    fun_name, func = self.get_function_at_line_ast_python(source_bef, cg['line_number'])
                    if fun_name != None:
                        if fun_name not in f_bef:
                            f_bef[fun_name] = {}
                            f_bef[fun_name]['code'] = func
                            f_bef[fun_name]['removed'] = list()
                        f_bef[fun_name]['removed'].append(f"-    {cg['line_number']}:{cg['content']}")
                    else:
                        pass   #TODO  同一个文件内可能有不在函数内的删减，这种情况应该定位某些行数保留下来

                if cg['type'] == 'added' and source_now is not None:
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


class GoAnalysis(DealMdic):
    def __init__(self, y, m, mdic):
        super().__init__(y, m, mdic)
        self.analyz()
        self.store_result()

    def analyz(self):
        for pf in self.patch_files:
            changes = self.get_changed_statements(pf[0])
            prev_commit = self.get_previous_commit(pf[1])
            source_bef = self.get_code_at_commit(self.repos_dir, prev_commit, pf[1]) if prev_commit else None
            source_now = self.get_code_at_commit(self.repos_dir, self.commit_id, pf[1])
            
            f_bef = dict()
            f_now = dict()
            for cg in changes:

                if cg['type'] == 'removed' and source_bef is not None:
                    fun_name, func = self.get_function_at_line_go(source_bef, cg['line_number'])
                    if fun_name != None:
                        if fun_name not in f_bef:
                            f_bef[fun_name] = {}
                            f_bef[fun_name]['code'] = func
                            f_bef[fun_name]['removed'] = list()
                        f_bef[fun_name]['removed'].append(f"-    {cg['line_number']}:{cg['content']}")
                    else:
                        pass   #TODO  同一个文件内可能有不在函数内的删减，这种情况应该定位某些行数保留下来

                if cg['type'] == 'added' and source_now is not None:
                    fun_name, func = self.get_function_at_line_go(source_now, cg['line_number'])
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
        self.store_result()

    def analyz(self):
        for pf in self.patch_files:
            changes = self.get_changed_statements(pf[0])
            prev_commit = self.get_previous_commit(pf[1])
            source_bef = self.get_code_at_commit(self.repos_dir, prev_commit, pf[1]) if prev_commit else None
            source_now = self.get_code_at_commit(self.repos_dir, self.commit_id, pf[1])
            
            f_bef = dict()
            f_now = dict()
            for cg in changes:

                if cg['type'] == 'removed' and source_bef is not None:
                    fun_name, func = self.get_function_at_line_cpp(source_bef, cg['line_number'])
                    if fun_name != None:
                        if fun_name not in f_bef:
                            f_bef[fun_name] = {}
                            f_bef[fun_name]['code'] = func
                            f_bef[fun_name]['removed'] = list()
                        f_bef[fun_name]['removed'].append(f"-    {cg['line_number']}:{cg['content']}")
                    else:
                        pass   #TODO  同一个文件内可能有不在函数内的删减，这种情况应该定位某些行数保留下来

                if cg['type'] == 'added' and source_now is not None:
                    fun_name, func = self.get_function_at_line_cpp(source_now, cg['line_number'])
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

    def get_function_at_line_cpp(self, source, target_line):
        """
        Extract the complete C/C++ function that contains the target line number.
        The returned function code includes line numbers.

        Args:
            source (str): The C/C++ source code as a string.
            target_line (int): The line number to locate (1-based).

        Returns:
            tuple[str, str] or None: A (function_name, function_code_with_lineno) tuple if found, else None.
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
        
        start = best_match['start'] - 1  # 0-based index
        end = best_match['end']          # inclusive in splitlines
        
        # Add line numbers
        func_lines = [
            f"{i + 1:>5}: {line}" for i, line in enumerate(lines[start:end], start=start)
        ]
        func_code = '\n'.join(func_lines)
        
        return best_match['name'], func_code


class PhpAnalysis(DealMdic):
    def __init__(self, y, m, mdic):
        super().__init__(y, m, mdic)
        self.analyz()
        self.store_result()

    def analyz(self):
        for pf in self.patch_files:
            changes = self.get_changed_statements(pf[0])
            prev_commit = self.get_previous_commit(pf[1])
            source_bef = self.get_code_at_commit(self.repos_dir, prev_commit, pf[1]) if prev_commit else None
            source_now = self.get_code_at_commit(self.repos_dir, self.commit_id, pf[1])
            
            f_bef = dict()
            f_now = dict()
            for cg in changes:

                if cg['type'] == 'removed' and source_bef is not None:
                    fun_name, func = self.get_function_at_line_php(source_bef, cg['line_number'])
                    if fun_name != None:
                        if fun_name not in f_bef:
                            f_bef[fun_name] = {}
                            f_bef[fun_name]['code'] = func
                            f_bef[fun_name]['removed'] = list()
                        f_bef[fun_name]['removed'].append(f"-    {cg['line_number']}:{cg['content']}")
                    else:
                        pass   #TODO  同一个文件内可能有不在函数内的删减，这种情况应该定位某些行数保留下来

                if cg['type'] == 'added' and source_now is not None:
                    fun_name, func = self.get_function_at_line_php(source_now, cg['line_number'])
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
                # lprinty(pf[0])
                if pf[1] not in self.result:
                    self.result[pf[1]] = {}
                self.result[pf[1]]['patch'] = pf[0]

    def get_function_at_line_php(self, source, target_line):
        """
        Extract the complete PHP function that contains the target line number.
        The returned function code includes line numbers.

        Args:
            source (str): The PHP source code as a string.
            target_line (int): The line number to locate (1-based).

        Returns:
            tuple[str, str] or None: A (function_name, function_code_with_lineno) tuple if found, else None.
        """
        import re
        
        lines = source.splitlines()
        if target_line > len(lines) or target_line < 1:
            return None, None

        # 更简化且更准确的PHP函数检测
        best_match = None
        best_start = -1
        
        # 从头开始扫描，寻找包含目标行的函数
        for i, line in enumerate(lines):
            # 简化的函数模式匹配，支持多种PHP函数定义
            patterns = [
                # 带修饰符的函数：public/private/protected/static等
                r'^\s*(?:(?:public|private|protected|final|abstract|static)\s+)+function\s+(\w+)',
                # 普通函数
                r'^\s*function\s+(\w+)',
                # 匿名函数赋值
                r'^\s*\$\w+\s*=\s*function\s*\(',
            ]
            
            func_name = None
            for pattern in patterns:
                match = re.search(pattern, line)
                if match:
                    if pattern.startswith(r'^\s*\$'):  # 匿名函数
                        func_name = f"anonymous_line_{i+1}"
                    else:
                        func_name = match.group(1)
                    break
            
            if func_name:
                start_line = i + 1
                
                # 寻找函数的结束位置
                end_line = self._find_php_function_end(lines, i)
                
                # 检查目标行是否在此函数内
                if start_line <= target_line <= end_line:
                    if start_line > best_start:  # 选择最内层的函数
                        best_match = {
                            'name': func_name,
                            'start': start_line,
                            'end': end_line
                        }
                        best_start = start_line
        
        if not best_match:
            return None, None
        
        # 提取函数代码并添加行号
        start = best_match['start'] - 1  # 转换为0-based索引
        end = best_match['end']
        
        func_lines = [
            f"{i + 1:>5}: {line}" for i, line in enumerate(lines[start:end], start=start)
        ]
        func_code = '\n'.join(func_lines)
        
        # 检查是否在类中
        class_name = self._find_php_class_context(lines, best_match['start'] - 1)
        if class_name:
            display_name = f"{class_name}.{best_match['name']}"
            func_code = f"# Class: {class_name}\n{func_code}"
        else:
            display_name = best_match['name']
        
        return display_name, func_code
    
    def _find_php_function_end(self, lines, start_idx):
        """寻找PHP函数的结束行"""
        brace_count = 0
        found_opening = False
        
        for i in range(start_idx, len(lines)):
            line = lines[i]
            # 跳过字符串中的大括号
            in_string = False
            escape_next = False
            
            for char in line:
                if escape_next:
                    escape_next = False
                    continue
                    
                if char == '\\':
                    escape_next = True
                    continue
                    
                if char in ['"', "'"]:
                    in_string = not in_string
                    continue
                    
                if not in_string:
                    if char == '{':
                        brace_count += 1
                        found_opening = True
                    elif char == '}':
                        brace_count -= 1
                        if found_opening and brace_count == 0:
                            return i + 1  # 返回1-based行号
        
        # 如果没有找到匹配的结束大括号，返回文件末尾
        return len(lines)
    
    def _find_php_class_context(self, lines, func_start_idx):
        """查找PHP函数所在的类"""
        import re
        
        class_brace_count = 0
        current_class = None
        
        for i in range(func_start_idx + 1):  # 从开头到函数开始处
            line = lines[i]
            
            # 检查类定义
            class_match = re.search(r'^\s*(?:(?:final|abstract)\s+)?class\s+(\w+)', line)
            if class_match:
                current_class = class_match.group(1)
                class_brace_count = 0
                continue
            
            # 计算大括号层级
            class_brace_count += line.count('{') - line.count('}')
            
            # 如果大括号层级回到0，说明离开了类
            if class_brace_count <= 0:
                current_class = None
        
        return current_class if class_brace_count > 0 else None



if __name__ == '__main__':
    pa = PyhtonAnalysis(2025, 5, "zzz")