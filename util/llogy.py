class Colors:

    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    
    
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'
    
    
    RESET = '\033[0m'  
    BOLD = '\033[1m'   
    UNDERLINE = '\033[4m'  
    REVERSE = '\033[7m' 

__colors__ = [v for key, v in vars(Colors).items() if not key.startswith('__') and isinstance(v, str)] 

class LogLeve:
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4
    NONE = 999 

class Llogy:
    
    _enable_leve = LogLeve.INFO

    @classmethod
    def set_leve(cls, leve: LogLeve):
        """
        leve must be one of the LogLeve.DEBUG .INFO .WARNING .ERROR .CRITICAL .NONE
        """
        cls._enable_leve = leve

    @classmethod
    def should_log(cls):
        return cls._enable_leve < LogLeve.NONE
    
    @classmethod
    def should_DEBUG(cls):
        return cls._enable_leve <= LogLeve.DEBUG
    
    @classmethod
    def should_INFO(cls):
        return cls._enable_leve <= LogLeve.INFO
    
    @classmethod
    def should_WARNING(cls):
        return cls._enable_leve <= LogLeve.WARNING
    
    @classmethod
    def should_ERROR(cls):
        return cls._enable_leve <= LogLeve.ERROR
    
    @classmethod
    def should_CRITICAL(cls):
        return cls._enable_leve <= LogLeve.CRITICAL


def lprinty(text: str, *color_args):
    """
    print text in color
    
    :param text: text that to be print
    :param color_args: one or more color styles. must be Colors.BLACK .BG_BLACK...
    """
    if not Llogy.should_log():

        return 
    if color_args == ():
        import inspect
        current_frame = inspect.currentframe()
        frame = current_frame.f_back
        if frame:
            lineno = frame.f_lineno
            filename = frame.f_code.co_filename
        del frame
        print(f"{Colors.BLUE}lprinty:{Colors.RESET} {Colors.GREEN} {text} {Colors.RESET} at {filename}: line {lineno}")
        return

    for color in color_args:
        if color not in __colors__:
            print(f'{Colors.RED}attention: {Colors.RESET} please cheack the params of lprinty')
            return
    print(f"{''.join(color_args)}{text}{Colors.RESET}")
    


def lprinty_structure(py_obj):
    """
    print the structure of a python object

    :param py_obj: python object must be one of Dict, List set
    """
    if Llogy.should_log() != True:
        return
    
    visited = list()

    def pprint(obj, dpt, no_space = False):
        def print1(s):
            txt = '    ' * dpt + s
            print(txt)
        def print2(s, end):
            txt = '    ' * dpt + '  ' + s
            print(txt, end=end)

        if id(obj) in visited:
            if no_space:
                print(f" '{type(obj).__name__}'")
            else:
                print1(f"'{type(obj).__name__}'")
            return

        visited.append(id(obj))

        if isinstance(obj, dict):
            if no_space:
                print('{')
            else:
                print1('{')
            for key, value in obj.items():
                print2(f"'{key}'" + ':', end='')
                pprint(value, dpt + 1, True)
            print1('}')
        elif isinstance(obj, list):
            if no_space:
                print('[')
            else:
                print1('[')
            for elm in obj:
                pprint(elm, dpt + 1)
            print1(']')

        elif isinstance(obj, set):
            if no_space:
                print('(')
            else:
                print1('(')
            for elm in obj:
                pprint(elm)
            print1(')')

        else:
            if no_space:
                print(f" '{type(obj).__name__}'")
            else:
                print1(f"'{type(obj).__name__}'")
    
    pprint(py_obj, 0)

def lprinty_line(text: str, *colorargs):
    lprinty(text, *colorargs)
    import inspect
    import linecache

    current_frame = inspect.currentframe()
    frame = current_frame.f_back.f_back
    if frame:
        lineno = frame.f_lineno
        filename = frame.f_code.co_filename
        line = linecache.getline(filename, lineno).strip()
        txt = f'{line} at {filename}: line {lineno}'
        lprinty(txt, Colors.YELLOW)
    del frame

def critical(text):
    lprinty(text, Colors.RED)
    import inspect
    import linecache

    current_frame = inspect.currentframe()
    frame = current_frame.f_back
    if frame:
        lineno = frame.f_lineno
        filename = frame.f_code.co_filename
        line = linecache.getline(filename, lineno - 1).strip()
        txt = f'{line} at {filename}: line {lineno}'
        lprinty(txt, Colors.RED)
    del frame
    exit(0)

if __name__ == "__main__":
    lprinty_line("call from main", Colors.RED)