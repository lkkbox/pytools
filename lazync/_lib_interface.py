import netCDF4 as nc
import numpy as np

# ---- metadata readers
def get_var_names(h:nc.Dataset) -> tuple[str]:
    return tuple(h.variables.keys())


def get_att_names(h:nc.Dataset, varName:str) -> tuple[str]:
    if varName == '/': # file root attributes
        hVar = h
    else:                     
        hVar = h[varName]

    return tuple(hVar.ncattrs())


# ---- readers
def read_var_all(h:nc.Dataset, varName:str) -> np.ndarray:
    return np.array(h[varName][:])

def read_var_slices(h:nc.Dataset, varName:str, slices:list[slice]) -> np.ndarray:
    return np.array(h[varName][slices])


def read_att(h:nc.Dataset, varName:str, attName:str) -> np.ndarray:
    if varName == '/': # file root attributes
        hVar = h
    else:                     
        hVar = h[varName]
    return hVar.getncattr(attName)
