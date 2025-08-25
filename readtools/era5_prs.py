from .. import timetools as tt
from ..plottools import FlushPrinter as Fp
from . import readtools as rt
import numpy as np


# constant settings begin
def getRootDir():
    return '/nwpr/gfs/com120/9_data/ERA5'


def getNcVarName(varName):
    if varName == 'vp':
        return 'velopot'
    elif varName == 'sf':
        return 'stream'
    else:
        return varName 
# constant settings end


def readTotal(varName, minMaxX, minMaxY, minMaxZ, minMaxT):

    numMonths = (tt.year(minMaxT[1]) - tt.year(minMaxT[0])) * 12
    numMonths += tt.month(minMaxT[1]) - tt.month(minMaxT[0]) + 1

    NT = int(minMaxT[1] - minMaxT[0] + 1)
    TIME = np.r_[minMaxT[0]:(minMaxT[1]+1)]

    fp = Fp()
    for imonth in range(numMonths):
        fp.flushPrint(f'ERA5 {imonth+1} / {numMonths}')
        
        t = tt.addMonth(minMaxT[0], imonth)
        year, month = tt.year(t), tt.month(t)

        dataSlice, timeSlice, lev, lat, lon = rt.readw2g(**{
            'filename': f'{getRootDir()}/daymean/PRS/{varName}/ERA5_{varName}_{year:04d}{month:02d}_r720x360_1day.nc',
            'varName': getNcVarName(varName),
            'minMaxs': [minMaxT, minMaxZ, minMaxY, minMaxX],
            'iDimT': 0,
            'minTime': tt.ymd2float(year, month, 1),
            'intervalTime': [1, 'day'],
        })

        nt = len(timeSlice)
        if imonth == 0: # initilize it
            nx, ny, nz = len(lon), len(lat), len(lev)
            data = np.nan * np.ones((NT, nz, ny, nx))
        
        tStart = np.where(TIME == timeSlice[0])[0][0]
        data[tStart:(tStart+nt), :] = dataSlice

    fp.flushPrint('')

    if varName == 'z':
        data /= 9.80665  # m2/s2 -> m

    return data, [TIME, lev, lat, lon]


def readClim(varName, minMaxX, minMaxY, minMaxZ, minMaxT=[0, 365], climYears=[2006, 2020], climType='3harm'):
    strClimYears = '_'.join(str(y) for y in climYears)
    
    it = [int(tt.dayOfYear(int(t))) - 1 for t in np.r_[minMaxT[0]:minMaxT[1]+1]]
    minMaxT = [min(it), max(it)]
    var, time, lev, lat, lon = rt.readw2g(**{
        'filename': f'{getRootDir()}/clim_{climType}/ERA5_{varName}_clim_{strClimYears}_r720x360_{climType}.nc',
        'varName': getNcVarName(varName),
        'minMaxs': [minMaxT, minMaxZ, minMaxY, minMaxX],
        'iDimT': 0,
        'minTime': tt.ymd2float(2000, 1, 1),
        'intervalTime': [1, 'day'],
    })

    if varName == 'z':
        var /= 9.80665  # m2/s2 -> m
        
    return var, [time, lev, lat, lon]


def readAnomaly(varName, minMaxX, minMaxY, minMaxZ, minMaxT, climYears=[2006, 2020], climType='3harm'):
    var_clim, dims_clim = readClim(
        varName=getNcVarName(varName),
        minMaxX=minMaxX,
        minMaxY=minMaxY,
        minMaxZ=minMaxZ,
        minMaxT=[0, 365],
        climYears=climYears,
        climType=climType,
    )
    time_clim, lev_clim, lat_clim, lon_clim = dims_clim

    # read total
    var_total, dims_total = readTotal(
        varName=getNcVarName(varName),
        minMaxX=minMaxX,
        minMaxY=minMaxY,
        minMaxZ=minMaxZ,
        minMaxT=minMaxT,
    )
    time_total, lev_total, lat_total, lon_total = dims_total

    if not np.array_equal(lon_clim, lon_total):
        raise Exception(' lon are mismatched')
    if not np.array_equal(lat_clim, lat_total):
        raise Exception(' lat are mismatched')

    # calculate anomalies
    var_anom = rt.cal_anomalies_366days(var_total, time_total, var_clim)
    return var_anom, [time_total, lev_total, lat_total, lon_total]

