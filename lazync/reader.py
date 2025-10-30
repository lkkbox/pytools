from . import _lib_interface as lib
import netCDF4 as nc
import numpy as np
import os


def _error_if_not_file(path:str) -> None:
    if not os.path.isfile(os.path.realpath(path)):
        raise FileNotFoundError(f'{path=}')


def _error_if_not_variable(h:nc.Dataset, varName:str) -> None:
    if varName not in lib.get_var_names(h):
        raise KeyError(f'{varName=} not found in {h.path=}')


def _error_if_not_attribute(h:nc.Dataset, varName:str, attName:str) -> None:
    if attName not in lib.get_att_names(h):
        raise KeyError(f'{attName=} not found for {varName=} in {h.path=}')


def read_var(
    path:str, 
    varName:str, 
    slices:None | list[slice]=None
) -> np.ndarray:

    _error_if_not_file(path)

    with nc.Dataset(path, 'r') as h:

        _error_if_not_variable(h, varName)

        if slices is None:
            read = lib.read_var_all
        else:
            read = lib.read_var_slices

        return read(h, varName)


def readatt(
    path:str, 
    varName:str, 
) -> str | int | float:

    _error_if_not_file(path)

    with nc.Dataset(path, 'r') as h:
        _error_if_not_variable(h, varName)
        _error_if_not_attribute(h, varName, attName)
        return lib.read_att(h, varName, attName)
