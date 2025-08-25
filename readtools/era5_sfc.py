from .. import timetools as tt
from ..plottools import FlushPrinter as Fp
from ..caltools import getContinuousIntegersIntervals
from . import readtools as rt
import numpy as np


def readTotal(varName, minMaxX, minMaxY, minMaxT):

    numYears = tt.year(minMaxT[1]) - tt.year(minMaxT[0]) + 1

    NT = int(minMaxT[1] - minMaxT[0] + 1)
    TIME = np.r_[minMaxT[0]:(minMaxT[1]+1)]

    fileNameFormat = getFileNameFormat(varName)

    fp = Fp()
    for iYear in range(numYears):
        year = tt.year(minMaxT[0]) + iYear
        fp.flushPrint(f'reading ERA5 {year} ({iYear}/{numYears})')
        # print(f'reading ERA5 {year} ({iYear}/{numYears})')
        

        dataSlice, timeSlice, lat, lon = rt.readw2g(**{
            'filename': fileNameFormat.format(year=year),
            'varName': getNCvarName(varName),
            'minMaxs': [minMaxT, minMaxY, minMaxX],
            'iDimT': 0,
            'minTime': tt.ymd2float(year, 1, 1),
            'intervalTime': [1, 'day'],
        })

        nt = len(timeSlice)
        if iYear == 0: # initilize it
            nx, ny = len(lon), len(lat)
            data = np.nan * np.ones((NT, ny, nx))
        
        tStart = np.where(TIME == timeSlice[0])[0][0]
        data[tStart:(tStart+nt), :] = dataSlice

    fp.flushPrint('')

    if varName == 'mslp':
        data /= 100

    return data, [TIME, lat, lon]


def readClim(varName, minMaxX, minMaxY, minMaxT=[0, 365], climYears=[2006, 2020], climType='3harm'):
    strClimYears = '_'.join(str(y) for y in climYears)
    if varName in ['u10', 'v10', 't2m', 'mslp']:
        fileName = f'/nwpr/gfs/com120/9_data/ERA5/clim_{climType}/ERA5_sfc_clim_{strClimYears}_{climType}.nc'
    elif varName in ['pw', 'tcwv']:
        fileName = f'/nwpr/gfs/com120/9_data/ERA5/clim_{climType}/ERA5_tcwv_clim_{strClimYears}_{climType}.nc'
    else:
        raise ValueError(f'{varName = } is not implemented yet')
    
    it = [int(tt.dayOfYear(int(t))) - 1 for t in np.r_[minMaxT[0]:minMaxT[1]+1]]
    minMaxT = [min(it), max(it)]
    data, time, lat, lon = rt.readw2g(**{
        'filename': fileName,
        'varName': getNCvarName(varName),
        'minMaxs': [minMaxT, minMaxY, minMaxX],
        'iDimT': 0,
        'minTime': tt.ymd2float(2000, 1, 1),
        'intervalTime': [1, 'day'],
    })

    if varName == 'mslp':
        data /= 100

    return data, [time, lat, lon]


def readAnomaly(varName, minMaxX, minMaxY, dates, climYears=[2006, 2020], climType='3harm'):
    data_clim, dims_clim = readClim(
        varName=varName,
        minMaxX=minMaxX,
        minMaxY=minMaxY,
        minMaxT=[0, 365],
        climYears=climYears,
        climType=climType,
    )
    time_clim, lat_clim, lon_clim = dims_clim

    dateBreakers = getContinuousIntegersIntervals(dates)

    fp = Fp()
    data_total, dims_total = None, None
    for dateBreaker in dateBreakers:
        fp.flushPrint(f'reading {varName} {[tt.float2format(d) for d in dateBreaker]}')
        varSlice, dimSlice = readTotal(
            varName=varName,
            minMaxX=minMaxX,
            minMaxY=minMaxY,
            minMaxT=dateBreaker,
        )

        if data_total is None:
            data_total = varSlice
            dims_total = dimSlice
        else:
            data_total = np.concatenate(
                (data_total, varSlice), axis=0
            )
            dims_total[0] = np.concatenate(
                (dims_total[0], dimSlice[0]), axis=0
            )
    fp.flushPrint('')

    # read total
    time_total, lat_total, lon_total = dims_total

    if not np.array_equal(lon_clim, lon_total):
        raise Exception(' lon are mismatched')
    if not np.array_equal(lat_clim, lat_total):
        raise Exception(' lat are mismatched')

    # calculate anomalies
    var_anom = rt.cal_anomalies_366days(data_total, time_total, data_clim)
    return var_anom, [time_total, lat_total, lon_total]


def getFileNameFormat(varName):
    if varName in ['pw', 'tcwv']:
        return '/nwpr/gfs/com120/9_data/ERA5/daymean/SFC/ERA5_tcwv_{year:04d}_day.nc'
    elif varName in ['u10', 'v10', 't2m', 'mslp']:
        return '/nwpr/gfs/com120/9_data/ERA5/daymean/SFC/ERA5_sfc_{year:04d}_day.nc'
    else:
        raise ValueError(f'unrecognized {varName = }')
    
def getNCvarName(varName):
    if varName in ['u10', 'v10', 't2m']:
        return varName
    elif varName in ['pw', 'tcwv']:
        return 'tcwv'
    elif varName == 'mslp':
        return 'msl'
    else:
        raise ValueError(f'unrecognized {varName = }')
