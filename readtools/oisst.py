from .. import timetools as tt
from ..plottools import FlushPrinter as Fp
from ..caltools import getContinuousIntegersIntervals
from . import readtools as rt
import numpy as np


def readTotal(minMaxX, minMaxY, minMaxT):
    def getFileName(year):
        return f'/nwpr/gfs/com120/9_data/OISST/v_2p1/daymean/sst.day.mean.{year}.nc'

    varName = 'sst'
    numYears = tt.year(minMaxT[1]) - tt.year(minMaxT[0]) + 1

    NT = int(minMaxT[1] - minMaxT[0] + 1)
    TIME = np.r_[minMaxT[0]:(minMaxT[1]+1)]

    fp = Fp()
    for iYear in range(numYears):
        year = tt.year(minMaxT[0]) + iYear
        fp.flushPrint(f'reading OISST {year} ({iYear}/{numYears})')

        dataSlice, timeSlice, lat, lon = rt.readw2g(**{
            'filename': getFileName(year),
            'varName': varName,
            'minMaxs': [minMaxT, minMaxY, minMaxX],
            'iDimT': 0,
            'minTime': tt.ymd2float(year, 1, 1),
            'intervalTime': [1, 'day'],
        })

        nt = len(timeSlice)
        if iYear == 0:  # initilize it
            nx, ny = len(lon), len(lat)
            data = np.nan * np.ones((NT, ny, nx))

        tStart = np.where(TIME == timeSlice[0])[0][0]
        data[tStart:(tStart+nt), :] = dataSlice

    fp.flushPrint('')

    if varName == 'mslp':
        data /= 100

    return data, [TIME, lat, lon]


def readClim(minMaxX, minMaxY, minMaxT=[0, 365], climYears=[2006, 2020], climType='3harm'):
    varName = 'sst'
    strClimYears = '-'.join(str(y) for y in climYears)
    fileName = f'/nwpr/gfs/com120/9_data/OISST/v_2p1/clim/sst.day.mean.v2.clim.{strClimYears}_{climType}.nc'

    it = [int(tt.dayOfYear(int(t))) -
          1 for t in np.r_[minMaxT[0]:minMaxT[1]+1]]
    minMaxT = [min(it), max(it)]
    data, time, lat, lon = rt.readw2g(**{
        'filename': fileName,
        'varName': varName,
        'minMaxs': [minMaxT, minMaxY, minMaxX],
        'iDimT': 0,
        'minTime': tt.ymd2float(2000, 1, 1),
        'intervalTime': [1, 'day'],
    })

    return data, [time, lat, lon]


def readAnomaly(minMaxX, minMaxY, dates, climYears=[2006, 2020], climType='3harm'):
    data_clim, dims_clim = readClim(
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
        fp.flushPrint(
            f'reading sst {[tt.float2format(d) for d in dateBreaker]}')
        varSlice, dimSlice = readTotal(
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