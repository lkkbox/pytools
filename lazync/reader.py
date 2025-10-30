from . import _lib_interface as lib
import netCDF4 as nc
import numpy as np
import os


def read(
    path:str, 
    varName:str, 
    slices:None | list[slice]=None
) -> np.ndarray:

    if not os.path.isfile(os.path.realpath(path)):
        raise FileNotFoundError(f'{path=}')

    with nc.Dataset(path, 'r') as h:
        if varName not in lib.get_var_names(h):
            raise KeyError(f'{varName=} not found in {path=}')
        return lib.read_all(h, varName)
