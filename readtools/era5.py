from .. import timetools as tt
from ..plottools import FlushPrinter as Fp
from . import readtools as rt
import numpy as np


def era5_fileVarName_to_ncVarName(varName):
    if varName in ['u200', 'u850']:
        return 'u'
    elif varName in ['v200', 'v850']:
        return 'v'
    elif varName in ['z500']:
        return 'z'
    elif varName in ['vp200', 'vp850']:
        return 'velopot'
    elif varName in ['sf200', 'sf850']:
        return 'stream'
    else:
        raise ValueError(f'unrecognized varName "{varName}"')


def era5_3dVar_clim_day_0p5(varName, minMaxX, minMaxY, minMaxT=[0, 365], climYears=[2006, 2020], climType='3harm'):
    minMaxT2000 = [tt.ymd2float(2000, tt.month(t), tt.day(t)) for t in minMaxT]
    ncVarName = era5_fileVarName_to_ncVarName(varName)
    var, time, lat, lon = rt.readw2g(**{
        'filename': f'/nwpr/gfs/com120/9_data/ERA5/clim_{climType}/ERA5_{varName}_clim_{climYears[0]}_{climYears[1]}_r720x360_{climType}.nc',
        'varName': ncVarName,
        'minMaxs': [minMaxT2000, minMaxY, minMaxX],
        'iDimT': 0,
        'minTime': tt.ymd2float(2000, 1, 1),
        'intervalTime': [1, 'day'],
    })
    if ncVarName == 'z':
        var /= 9.80665  # m2/s2 -> m
    return var, [time, lat, lon]



def era5_3dVar_total_day_0p5(varName, minMaxX, minMaxY, minMaxT):
    nmonths = (tt.year(minMaxT[1]) - tt.year(minMaxT[0])) * 12
    nmonths += tt.month(minMaxT[1]) - tt.month(minMaxT[0]) + 1
    ncVarName = era5_fileVarName_to_ncVarName(varName)
    fp = Fp()
    for imonth in range(nmonths):
        fp.flushPrint(f' {imonth+1} / {nmonths}')
        t = tt.addMonth(minMaxT[0], imonth)
        year, month = tt.year(t), tt.month(t)
        varSlice, timeSlice, lat, lon = rt.readw2g(**{
            'filename': f'/nwpr/gfs/com120/9_data/ERA5/daymean/{varName}/ERA5_{varName}_{year}{month:02d}_r720x360_1day.nc',
            'varName': ncVarName,
            'minMaxs': [minMaxT, minMaxY, minMaxX],
            'iDimT': 0,
            'minTime': tt.ymd2float(year, month, 1),
            'intervalTime': [1, 'day'],
        })
        if imonth == 0:
            var = varSlice
            time = timeSlice
        else:
            var = np.concatenate((var, varSlice), axis=0)
            time = np.concatenate((time, timeSlice), axis=0)
    fp.flushPrint('')
    if ncVarName == 'z':
        var /= 9.80665  # m2/s2 -> m

    return var, [time, lat, lon]


def era5_u200_clim_day_0p5(minMaxX, minMaxY, minMaxT=[-np.inf, np.inf], climYears=[2006, 2020], climType='3harm'):
    var, time, lat, lon = rt.readw2g(**{
        'filename': f'/nwpr/gfs/com120/9_data/ERA5/clim_{climType}/ERA5_u200_clim_{climYears[0]}_{climYears[1]}_r720x360_{climType}.nc',
        'varName': 'u',
        'minMaxs': [minMaxT, minMaxY, minMaxX],
        'iDimT': 0,
        'minTime': tt.ymd2float(2000, 1, 1),
        'intervalTime': [1, 'day'],
    })
    return var, [time, lat, lon]


def era5_u850_clim_day_0p5(minMaxX, minMaxY, minMaxT=[-np.inf, np.inf], climYears=[2006, 2020], climType='3harm'):
    var, time, lat, lon = rt.readw2g(**{
        'filename': f'/nwpr/gfs/com120/9_data/ERA5/clim_{climType}/ERA5_u850_clim_{climYears[0]}_{climYears[1]}_r720x360_{climType}.nc',
        'varName': 'u',
        'minMaxs': [minMaxT, minMaxY, minMaxX],
        'iDimT': 0,
        'minTime': tt.ymd2float(2000, 1, 1),
        'intervalTime': [1, 'day'],
    })
    return var, [time, lat, lon]



def era5_u200_total_day_0p5(minMaxX, minMaxY, minMaxT):
    nmonths = (tt.year(minMaxT[1]) - tt.year(minMaxT[0])) * 12
    nmonths += tt.month(minMaxT[1]) - tt.month(minMaxT[0]) + 1
    for imonth in range(nmonths):
        t = tt.addMonth(minMaxT[0], imonth)
        year, month = tt.year(t), tt.month(t)
        varSlice, timeSlice, lat, lon = rt.readw2g(**{
            'filename': f'/nwpr/gfs/com120/9_data/ERA5/daymean/u200/ERA5_u200_{year}{month:02d}_r720x360_1day.nc',
            'varName': 'u',
            'minMaxs': [minMaxT, minMaxY, minMaxX],
            'iDimT': 0,
            'minTime': tt.ymd2float(year, month, 1),
            'intervalTime': [1, 'day'],
        })
        if imonth == 0:
            var = varSlice
            time = timeSlice
        else:
            var = np.concatenate((var, varSlice), axis=0)
            time = np.concatenate((time, timeSlice), axis=0)
    return var, [time, lat, lon]


def era5_u850_total_day_0p5(minMaxX, minMaxY, minMaxT):
    nmonths = (tt.year(minMaxT[1]) - tt.year(minMaxT[0])) * 12
    nmonths += tt.month(minMaxT[1]) - tt.month(minMaxT[0]) + 1
    for imonth in range(nmonths):
        t = tt.addMonth(minMaxT[0], imonth)
        year, month = tt.year(t), tt.month(t)
        varSlice, timeSlice, lat, lon = rt.readw2g(**{
            'filename': f'/nwpr/gfs/com120/9_data/ERA5/daymean/u850/ERA5_u850_{year}{month:02d}_r720x360_1day.nc',
            'varName': 'u',
            'minMaxs': [minMaxT, minMaxY, minMaxX],
            'iDimT': 0,
            'minTime': tt.ymd2float(year, month, 1),
            'intervalTime': [1, 'day'],
        })
        if imonth == 0:
            var = varSlice
            time = timeSlice
        else:
            var = np.concatenate((var, varSlice), axis=0)
            time = np.concatenate((time, timeSlice), axis=0)
    return var, [time, lat, lon]


def era5_u200_anom_day_0p5(minMaxX, minMaxY, minMaxT, climYears=[2006, 2020], climType='3harm'):
    var, dims = rt.read_anom(
        era5_u200_total_day_0p5,
        era5_u200_clim_day_0p5,
        minMaxX,
        minMaxY,
        minMaxT,
        climYears,
        climType
    )
    return var, dims


def era5_u850_anom_day_0p5(minMaxX, minMaxY, minMaxT, climYears=[2006, 2020], climType='3harm'):
    var, dims = rt.read_anom(
        era5_u850_total_day_0p5,
        era5_u850_clim_day_0p5,
        minMaxX,
        minMaxY,
        minMaxT,
        climYears,
        climType
    )
    return var, dims


def era5_3dVar_anom_day_0p5(varName, minMaxX, minMaxY, minMaxT, climYears=[2006, 2020], climType='3harm'):
    var_clim, dims_clim = era5_3dVar_clim_day_0p5(
        varName=varName,
        minMaxX=minMaxX,
        minMaxY=minMaxY,
        minMaxT=[0, 365],
        climYears=climYears,
        climType=climType,
    )
    time_clim, lat_clim, lon_clim = dims_clim

    # read total
    var_total, dims_total = era5_3dVar_total_day_0p5(
        varName=varName,
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
    var_anom = rt.cal_anomalies_366days(var_total, time_total, var_clim)
    return var_anom, [time_total, lat_total, lon_total]
