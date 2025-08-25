from .. import timetools as tt
from ..nctools import ncreadByDimRange
from ..caltools import interp_1d
from ..terminaltools import FlushPrinter as Fp
import numpy as np
import os

# ----------------------- #
# constant settings begin #


@lambda x: x()
def ERA5dir():
    return '/nwpr/gfs/com120/9_data/ERA5'


def _getNcVarName(varName):
    if varName == 'vp':
        return 'velopot'
    elif varName == 'sf':
        return 'stream'
    elif varName == 'pw':
        return 'tcwv'
    elif varName == 'mslp':
        return 'msl'
    else:
        return varName


def _getFileVarName(varName):
    if varName == 'pw':
        return 'tcwv'
    else:
        return varName


def _getFileName(varName, date):
    rootDir = f'{ERA5dir}/nearRealTime/daymean'
    fileVarName = _getFileVarName(varName)
    return tt.float2format(date, f'{rootDir}/ERA5_{fileVarName}_%Y%m%d_r720x360_1day.nc')
# constant settings end #
# --------------------- #


def dateIsAvail(varNames, date, throwError=False):
    if isinstance(varNames, str):
        varNames = [varNames]
    for varName in varNames:
        fileName = _getFileName(varName, date)
        if not os.path.exists(fileName) and throwError:
            raise FileNotFoundError(fileName)
        elif not os.path.exists(fileName):
            return False
    return True


def getLatestDate(varNames):
    if isinstance(varNames, str):
        varNames = [varNames]

    today = tt.today()
    for delay in range(999):
        date = today - delay
        if dateIsAvail(date):
            return date
    return None


def getAvailDateRange(varNames, dateRange):
    if isinstance(varNames, str):
        varNames = [varNames]

    date = dateRange[1]
    while date >= dateRange[0]:
        if dateIsAvail(varNames, date):
            dateMax = date
            break
        elif date == dateRange[0]:
            dateMax = None
        else:
            date -= 1

    date = dateRange[0]
    while date <= dateRange[1]:
        if dateIsAvail(varNames, date):
            dateMin = date
            break
        elif date == dateRange[1]:
            dateMin = None
        else:
            date += 1

    return [dateMin, dateMax]


def readTotal(varName, minMaxs):
    '''
    minMaxs = [
        timeRange#days_since_2000-01-01, 
        (levelRange#Pa(10_00-1000_00),) 
        latRange#degrees_north(-90-90), 
        lonRange#degrees_east(0-360)
    ]
    '''

    minMaxT = minMaxs[0]

    NT = int(minMaxT[1] - minMaxT[0] + 1)
    DATES = np.r_[minMaxT[0]:(minMaxT[1]+1)]

    fp = Fp()

    # Pa -> hPa
    minMaxs = _pa2hPa(minMaxs)

    # check file existence
    for iDate, date in enumerate(DATES):
        fp.flush(f'checking ERA5 {varName}.. ({iDate}/{NT})')
        if not dateIsAvail(varName, date, throwError=True):
            break

    ncVarName = _getNcVarName(varName)
    # read data
    for iDate, date in enumerate(DATES):
        fp.flush(f'reading ERA5 {varName}.. ({iDate}/{NT})')
        subData, subDims = ncreadByDimRange(
            fileName=_getFileName(varName, date),
            varName=ncVarName,
            minMaxs=[[t+0.25 for t in minMaxs[0]], *minMaxs[1:]],
        )           # shift time by 0.25 for daily mean of (00, 12)z

        # initialize
        if iDate == 0:
            data = np.nan * np.ones((NT, *subData.shape[1:]))
            if len(minMaxs) == 4:  # hPa -> Pa
                subDims[1] = [l*100 for l in subDims[1]]
            dims = [DATES, *subDims[1:]]

        data[iDate, :] = subData

    return data, dims


def readClim(varName, minMaxs, climYears, climType):
    if varName == 'pw':
        fileVarName = 'tcwv'
    elif varName not in ['u', 'v', 't', 'q', 'z']:
        fileVarName = 'sfc'
    else:
        fileVarName = varName

    if varName == 'pw':
        res = 'r360x180'
    else:
        res = 'r720x360'

    # Pa -> hPa
    minMaxs = _pa2hPa(minMaxs)

    strClimYears = '_'.join([str(y) for y in climYears])
    fileDir = f'{ERA5dir}/clim_{climType}'
    fileName = f'{fileDir}/' + \
        f'ERA5_{fileVarName}_clim_{strClimYears}_{res}_{climType}.nc'

    date0 = tt.ymd2float(2000, 1, 1)
    minMaxDOY = [tt.dayOfYear229(date) for date in minMaxs[0]] 
    if minMaxDOY[0] <= minMaxDOY[1]:
        minMaxT = [date0 + doy - 1 for doy in minMaxDOY]
    elif minMaxDOY[0] > minMaxDOY[1]:
        minMaxT = [date0 + doy - 1 for doy in [1, 366]]

    minMaxsCopy = minMaxs.copy()
    minMaxsCopy[0] = minMaxT

    data, dims = ncreadByDimRange(
        fileName=fileName,
        varName=_getNcVarName(varName),
        minMaxs=minMaxsCopy,
    )

    requestedDates = np.r_[minMaxs[0][0]:(minMaxs[0][1]+1)]
    requestedDOYs = [tt.dayOfYear229(d) for d in requestedDates]
    readDOYs = [tt.dayOfYear229(float(d)) for d in dims[0]]
    indices = [readDOYs.index(rdoy) for rdoy in requestedDOYs]

    data = data[indices, :]
    dims = [dims[0][indices], *dims[1:]]

    return data, dims


def readAnomaly(varName, minMaxs, climYears, climType):
    varTotal, dimsTotal = readTotal(varName, minMaxs)
    varClim, dimsClim = readClim(varName, minMaxs, climYears, climType)
    lonTotal, latTotal = dimsTotal[-1], dimsTotal[-2]
    lonClim, latClim = dimsClim[-1], dimsClim[-2]

    if not np.array_equal(lonTotal, lonClim):
        varClim = interp_1d(lonClim, varClim, lonTotal, -1, True)

    if not np.array_equal(latTotal, latClim):
        varClim = interp_1d(latClim, varClim, latTotal, -2, True)

    varAnom = varTotal - varClim
    return varAnom, dimsTotal



def _pa2hPa(minMaxs):
    minMaxs2 = minMaxs.copy()
    # Pa -> hPa
    if len(minMaxs2) == 4:
        minMaxs2[1] = [l/100 for l in minMaxs2[1]]
    return minMaxs2
