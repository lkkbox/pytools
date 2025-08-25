# [SOURCE]_[VARIABLE]_[TOTAL/ANOM/CLIM]_[TIME_RES]_[SPATIAL_RES]
import netCDF4 as nc
import numpy as np
from .. import timetools as tt
from .. import caltools as ct
from ..plottools import FlushPrinter as Fp


def readw2g(filename, varName, minMaxs, iDimT=None, minTime=None, intervalTime=[1, 'day']):

    def createTimeAxis():
        numTime = h[varName].shape[0]
        interval = intervalTime[0]
        unit = intervalTime[1]
        if unit == 'day':
            DIM = np.r_[minTime: minTime + numTime * interval: interval]
        elif unit == 'month':
            DIM = [tt.addMonth(minTime, i * interval) for i in range(numTime)]
            DIM = np.array(DIM)
        return np.array(DIM)

    if intervalTime[1] not in ['day', 'month']:
        raise ValueError('intervalTime must be "day" or "month"')
    
    for minMax in minMaxs:
        if len(minMax) != 2:
            raise ValueError(f'Elements in minMax must be 2 numbers, but received {minMax}')
        for e in minMax:
            if not (isinstance(e, float) or isinstance(e, int)):
                raise ValueError(f'Elements in minMax must be numbers, but received type={type(e)} value={e} in minMax={minMax}')

    # ==== main function here ====
    with nc.Dataset(filename, 'r') as h:
        indices, dims, idim_to_flip = [], [], []

        if len(minMaxs) != len(h[varName].dimensions):
            raise ValueError(
                f'Input minmaxs have {len(minMaxs)} elements, but the file has {
                    len(h[varName].dimensions)} dimensions.'
                + f' file name = {filename}'
            )

        # getting each dimension
        for iDim, dimName in enumerate(h[varName].dimensions):
            ndim = h[dimName].ndim

            if ndim > 1:
                raise Exception(f' cannot handle n-d dimension "{dimName}"')
            if iDim == iDimT:
                DIM = createTimeAxis()
            else:
                DIM = np.array(h[dimName][:])

            minIndex, maxIndex, numIndex, dim = ct.w2g(
                DIM, minMaxs[iDim][0], minMaxs[iDim][1])

            # when no values are found in boundaries            
            if minIndex is None:
                return None, *[None for __ in range(len(minMaxs))]

            if len(dim) > 1:
                if dim[0] > dim[1]:
                    dim = np.flip(dim)
                    idim_to_flip.append(iDim)

            indices.append(slice(minIndex, maxIndex))
            dims.append(np.array(dim))

        # getting the variable
        var = np.array(h[varName][indices])
        var = np.flip(var, axis=idim_to_flip)

    return var, *dims

# .... it only supports 3d variables ....
def read_anom(func_read_total, func_read_clim, minMaxX, minMaxY, minMaxT, climYears=[2006, 2020], climType='3harm'):
    var_clim, dims_clim = func_read_clim(
        minMaxX=minMaxX,
        minMaxY=minMaxY,
        minMaxT=[0, 365],
        climYears=climYears,
        climType=climType,
    )
    time_clim, lat_clim, lon_clim = dims_clim

    # read total
    var_total, dims_total = func_read_total(
        minMaxX=minMaxX,
        minMaxY=minMaxY,
        minMaxT=minMaxT,
    )

    time_total, lat_total, lon_total = dims_total

    if not np.array_equal(lon_clim, lon_total):
        raise Exception(' lon are mismatched')
    if not np.array_equal(lat_clim, lat_total):
        raise Exception(' lat are mismatched')

    # calculate anomalies
    var_anom = cal_anomalies_366days(var_total, time_total, var_clim)
    return var_anom, [time_total, lat_total, lon_total]


def cal_anomalies_366days(var_total, time_total, var_clim):
    iDaysOfYear = [t - tt.ymd2float(tt.year(t), 1, 1) for t in time_total]
    iDaysOfYear = [int(t) for t in iDaysOfYear]
    # days after Feb29 are added by 1
    iDaysOfYear = [t + 1 if t >
                   60 and not tt.isleap(t) else t for t in iDaysOfYear]
    return var_total - var_clim[iDaysOfYear, :]
