class FlushPrinter:
    def __init__(self):
        self.content = ''
        return

    def flush(self, new_string=''):
        new_string = str(new_string)
        self.flushPrint('')
        self.flushPrint(new_string)
        return
    
    def flushPrint(self, new_string=''):
        new_string = str(new_string)
        numErase = len(self.content)
        eraser = '\b'*numErase + ' '*numErase + '\b'*numErase
        print(eraser + new_string, flush=True, end='')
        self.content = new_string
        return

    def print(self, new_string='', **kwArgs):
        self.flush('')
        print(new_string, flush=True, **kwArgs)

    def appendPrint(self, new_string='', **kwArgs):
        self.content=''
        print(new_string, flush=True, **kwArgs)

    def printNewline(self, new_string='', **kwArgs):
        self.content=''
        print('\n' + new_string, flush=True, **kwArgs)

    def append(self, new_string=''):
        self.content += str(new_string)
        print(new_string, end='', flush=True)
        return

    def __del__(self):
        self.flush('')
