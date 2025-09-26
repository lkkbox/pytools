from .. import nctools as nct
from ..checktools import checkType
import numpy as np
import os


def _nc_sanity_check(path: str, varname: str, minmaxs: list[list[float | int]]) -> None:
    if not os.path.exists(path):
        raise FileNotFoundError(path)

    if varname not in nct.getVarNames(path):
        raise ValueError(f'{varname=} is not found in {path=}')

    shape = nct.getVarShape(path, varname)
    ndim = len(shape)
    if len(minmaxs) != ndim:
        raise ValueError(f'expected len(minmaxs)=ndim={ndim}, but recived {len(minmaxs)} for {varname=} in {path=}')


def read2d(
    path: str, varname: str, minmaxs: list[list[float | int]], idimxy: list[int] | tuple[int],
    iDimT: int | None=None, decodeTime=True, nanmean=True
) -> tuple[np.ndarray, list[np.ndarray]]:
    
    checkType(path, str, 'path')
    checkType(varname, str, 'varname')
    checkType(minmaxs, list, 'minmaxs')
    checkType(idimxy, list, 'idimxy')
    checkType(iDimT, [int, None], 'iDimT')
    checkType(decodeTime, bool, 'decodeTime')
    checkType(nanmean, bool, 'nanmean')
    for e in minmaxs:
        checkType(e, [list], 'elements in minmaxs')
        if len(e) != 2:
            raise ValueError(f'The length of elements in minmax must be 2 but found {len(e)}')
        for ee in e:
            checkType(ee, [float, int, None], 'element in the sublist of minmaxs')

    if len(idimxy) != 2:
        raise ValueError(f'len(idimxy) must be 2 but found {len(idimxy)}')

    for e in idimxy:
        checkType(e, int, 'elements in idimxy')

    _nc_sanity_check(path, varname, minmaxs)
    if nanmean:
        mean = np.nanmean
    else:
        mean = np.mean
    
    ndim = len(minmaxs)
    idimxy_pos = [i if i >= 0 else ndim + i for i in idimxy]
    idims_to_avg = tuple([i for i in range(ndim) if i not in idimxy_pos])

    data, dims = nct.ncreadByDimRange(
        path, varname, minmaxs, iDimT, decodeTime
    )

    data = mean(data, axis=idims_to_avg)
    dims = [dims[i] for i in idimxy_pos]

    if idimxy_pos[0] > idimxy_pos[1]:
        data = np.swapaxes(data, 0, 1)

    return data, dims
