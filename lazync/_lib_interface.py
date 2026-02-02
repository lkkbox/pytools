from netCDF4 import Dataset
import numpy as np
'''
pure wrapper for netCDF4.Dataset with minimum false save and without extra functionality
'''


# ---- metadata readers
def get_var_names(h: Dataset) -> tuple[str]:
    return tuple(h.variables.keys())


def get_att_names(h: Dataset, varName: str) -> tuple[str]:
    if varName == '/':  # file root attributes
        hVar = h
    else:
        hVar = h[varName]

    return tuple(hVar.ncattrs())


# ---- readers
def read_var_all(h: Dataset, varName: str) -> np.ndarray:
    return np.array(h[varName][:])


def read_var_slices(h: Dataset, varName: str, slices: list[slice]) -> np.ndarray:
    return np.array(h[varName][slices])


def read_att(h: Dataset, varName: str, attName: str) -> np.ndarray:
    if varName == '/':  # file root attributes
        hVar = h
    else:
        hVar = h[varName]
    return hVar.getncattr(attName)
