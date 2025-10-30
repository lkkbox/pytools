import netCDF4 as nc
import numpy as np

# ---- metadata readers
def get_var_names(h:nc.Dataset) -> tuple[str]:
    return tuple(h.variables.keys())


# ---- readers
def read_all(h:nc.Dataset, varName:str) -> np.ndarray:
    return np.array(h[varName][:])

