from .. import timetools as tt
from ..plottools import FlushPrinter as Fp
from . import readtools as rt
import numpy as np


def cbo_olr_total_day_2p5(minMaxX, minMaxY, minMaxT):
    var, time, lat, lon = rt.readw2g(**{
        'filename': '/nwpr/gfs/com120/9_data/NOAA_OLR/olr.cbo-2.5deg.day.mean.nc',
        'varName': 'olr',
        'minMaxs': [minMaxT, minMaxY, minMaxX],
        'iDimT': 0,
        'minTime': tt.ymd2float(1991, 1, 1),
        'intervalTime': [1, 'day'],
    })
    var[(np.abs(var) > 1e3)] = np.nan
    return var, [time, lat, lon]


def cbo_olr_total_day_1p0(minMaxX, minMaxY, minMaxT):
    var, time, lat, lon = rt.readw2g(**{
        'filename': '/nwpr/gfs/com120/9_data/NOAA_OLR/olr.cbo-1deg.day.mean.nc',
        'varName': 'olr',
        'minMaxs': [minMaxT, minMaxY, minMaxX],
        'iDimT': 0,
        'minTime': tt.ymd2float(1991, 1, 1),
        'intervalTime': [1, 'day'],
    })
    var[(np.abs(var) > 1e3)] = np.nan
    return var, [time, lat, lon]


def cbo_olr_clim_day_2p5(minMaxX, minMaxY, minMaxT=[-np.inf, np.inf], climYears=[2006, 2020], climType='3harm'):
    minMaxT2000 = [tt.ymd2float(2000, tt.month(t), tt.day(t)) for t in minMaxT]
    var, time, lat, lon = rt.readw2g(**{
        'filename': f'/nwpr/gfs/com120/9_data/NOAA_OLR/olr_clim_{climYears[0]}_{climYears[1]}_2p5_{climType}.nc',
        'varName': 'olr',
        'minMaxs': [minMaxT2000, minMaxY, minMaxX],
        'iDimT': 0,
        'minTime': tt.ymd2float(2000, 1, 1),
        'intervalTime': [1, 'day'],
    })
    var[(np.abs(var) > 1e3)] = np.nan
    return var, [time, lat, lon]


def cbo_olr_clim_day_1p0(minMaxX, minMaxY, minMaxT=[-np.inf, np.inf], climYears=[2006, 2020], climType='3harm'):
    minMaxT2000 = [tt.ymd2float(2000, tt.month(t), tt.day(t)) for t in minMaxT]
    var, time, lat, lon = rt.readw2g(**{
        'filename': f'/nwpr/gfs/com120/9_data/NOAA_OLR/olr_clim_{climYears[0]}_{climYears[1]}_1p0_{climType}.nc',
        'varName': 'olr',
        'minMaxs': [minMaxT2000, minMaxY, minMaxX],
        'iDimT': 0,
        'minTime': tt.ymd2float(2000, 1, 1),
        'intervalTime': [1, 'day'],
    })
    var[(np.abs(var) > 1e3)] = np.nan
    return var, [time, lat, lon]

def cbo_olr_anom_day_1p0(minMaxX, minMaxY, minMaxT, climYears=[2006, 2020], climType='3harm'):
    var, dims = rt.read_anom(
        cbo_olr_total_day_1p0,
        cbo_olr_clim_day_1p0,
        minMaxX,
        minMaxY,
        minMaxT,
        climYears,
        climType
    )
    return var, dims


def cbo_olr_anom_day_2p5(minMaxX, minMaxY, minMaxT, climYears=[2006, 2020], climType='3harm'):
    # [ calculate anomalies on the fly ]

    # read climatology
    var_clim, time_clim, lat_clim, lon_clim = cbo_olr_clim_day_2p5(
        minMaxX=minMaxX,
        minMaxY=minMaxY,
        minMaxT=[0, 365],
        climYears=climYears,
        climType=climType,
    )

    # read total
    var_total, time_total, lat_total, lon_total = cbo_olr_total_day_2p5(
        minMaxX=minMaxX,
        minMaxY=minMaxY,
        minMaxT=minMaxT,
    )

    if not np.array_equal(lon_clim, lon_total):
        raise Exception(' lon are mismatched')
    if not np.array_equal(lat_clim, lat_total):
        raise Exception(' lat are mismatched')

    # calculate anomalies
    var_anom = rt.cal_anomalies_366days(var_total, time_total, var_clim)
    return var_anom, [time_total, lat_total, lon_total]

