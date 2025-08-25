import os, inspect
from typing import Literal


def delete(fileName, verbose=False):
    cmd = '/nwpr/gfs/com120/0_tools/bashtools/del ' + fileName
    if verbose:
        print(cmd, flush=True)
    os.system(cmd)


def canBeWritten(fileName):
    fileExists = os.path.isfile(fileName)

    if not fileExists:
        os.system(f'touch {fileName}')
    fileCanBeWritten = os.access(fileName, os.W_OK)

    if not fileExists and fileCanBeWritten:
        os.system(f'/bin/rm {fileName}')

    return fileCanBeWritten

# ===============================
def getPyFileName():
    frame = inspect.stack()[-1]
    module = inspect.getmodule(frame[0])
    fileName = module.__file__
    fileName = fileName.replace(r'/./', r'/')
    return fileName

def getPyBaseName():
    return getPyFileName().split('/')[-1]

def getPyDirName():
    return '/'.join(getPyFileName().split('/')[:-1])

def getPyName():
    return ''.join(getPyBaseName().split('.')[:-1])

# ===============================
def getModuleFileName(shift=0):
    frame = inspect.stack()[1+shift]
    module = inspect.getmodule(frame[0])
    fileName = module.__file__
    fileName = fileName.replace(r'/./', r'/')
    return fileName

def getModuleBaseName():
    return getModuleFileName(1).split('/')[-1]

def getModuleDirName():
    return '/'.join(getModuleFileName(1).split('/')[:-1])

def getModuleName():
    return ''.join(getModuleFileName(1).split('/')[-1].split('.')[:-1])


# ===============================
def check_des_path(
    desPath:str, 
    makeParentDir:bool=True,
    throwError:bool=True,
    accepts:list=[0, 1],
) -> Literal[0, 1, 2, 3, 4]:
    '''
    0 -> path not exists but dir can be written
    1 -> path     exists and can be written
    2 -> path     exists but cannot be written
    3 -> dir not exists 
    4 -> dir cannot be written
    '''

    conditions = {
        0: 'path not exists but dir can be written',
        1: 'path     exists and can be written',
        2: 'path     exists but cannot be written',
        3: 'dir not exists ',
        4: 'dir cannot be written',
    }

    desDir = os.path.dirname(desPath)

    if not os.path.exists(desDir) and makeParentDir:
        os.system(f'mkdir -p {desDir}')

    desPathExists = os.path.exists(desPath)
    desPathWOK = os.access(desPath, os.W_OK)
    desDirExists = os.path.exists(desDir)
    desDirWOK = os.access(desDir, os.W_OK)

    if not desPathExists and desDirWOK:
        ret_code = 0
    elif desPathExists and desPathWOK:
        ret_code = 1
    elif desPathExists and not desPathWOK:
        ret_code = 2
    elif not desDirExists:
        ret_code = 3
    elif not desDirWOK:
        ret_code = 4
    else:
        raise RuntimeError(
            f'unable to determine ret_code with' +
            f'{desPathExists=}, {desPathWOK=}, {desDirExists=}, {desDirWOK=}'
        )

    if ret_code not in accepts and throwError:
        raise RuntimeError(f'{conditions[ret_code]}, {desPath = }')

    return ret_code

