from . import timetools as tt
import numpy as np
import os

def read2d(path, nxny, precision='double'):
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    
    if precision == 'double':
        dataType = np.float64
    elif precision in ['single', 'float']:
        dataType = np.float32
        
    data = np.fromfile(path, dtype=dataType, count=np.prod(nxny))
    data = np.reshape(data, nxny[::-1])

    return data


def readNd(paths, shape, precision='double'):
    notFoundPaths = [
        path for path in paths
        if not os.path.exists(path)
    ]
    if notFoundPaths:
        raise FileNotFoundError([' '.join(notFoundPaths)])
    data = np.array([read2d(path, shape[-2:], precision) for path in paths])
    data = np.reshape(data, shape)
    return data


def multiLevelVarName2dmsPrefix(varName, levels=None):
    if levels is not None:
        return [varName2dmsPrefix(varName, level) for level in levels]
    else:
        return [varName2dmsPrefix(varName)]


def varName2dmsPrefix(varName, level=None):
    if varName not in ['u', 'v', 'w', 't', 'q', 'z', 'r']: # 3d variables
        keys = {
            'u10': 'B10200',
            'v10': 'B10210',
            't2m': 'B02100',
            'pw': 'X00590',
            'mslp': 'SSL010',
            'prec': 'B00626',
            'olr': 'X0034F',
            'lh': 'S00430',
        }
        key = keys.get(varName)

    else: # 4d variables
        if level is None:
            raise ValueError(f'{varName=} but the level is None')

        if level == 1000:
            keyHead = 'H00'
        else:
            keyHead = f'{level:03d}'

        keyTails = {
            'u': '200',
            'v': '210',
            'w': '220',
            't': '100',
            'q': '500',
            'z': '000',
        }
        key = f'{keyHead}{keyTails.get(varName)}'

    if key is None:
        raise NotImplementedError(f'{varName = }, {level = }')

    else:
        return key
