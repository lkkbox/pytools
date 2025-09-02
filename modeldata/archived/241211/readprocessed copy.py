#!/nwpr/gfs/com120/.conda/envs/rd/bin/python
'''
This is a module for reading the reforecast of 
GEPSv3 (CFSR).
'''
from ..caltools import w2g
from ..caltools import interp_1d
from ..plottools import FlushPrinter as Fp
from .. import timetools as tt
from .. import readtools as rt
from copy import deepcopy
import numpy as np
import os


def getDimensions():
    LON = np.r_[0:360]
    LAT = np.r_[-89.5:90]
    LEV = 100 * np.r_[10, 30, 50, 100, 200, 300, 500, 700, 850, 925, 1000]
    return LON, LAT, LEV


def getNxNyNz( minMaxX, minMaxY, minMaxZ):
    LON, LAT, LEV = getDimensions()
    _, _, nx, lon = w2g(LON, *minMaxX)
    _, _, ny, lat = w2g(LAT, *minMaxY)
    _, _, nz, lev = w2g(LEV, *minMaxZ)
    return nx, ny, nz, lon, lat, lev


def readTotal3d(modelName, varName, minMaxX, minMaxY, minMaxLead, minMaxInit):
    if varName not in ['u10', 'v10', 't2m', 'prec', 'mslp', 'olr']:
        raise ValueError(f' unrecognized varName "{varName}", try readTotal4d?')
    return readTotal(modelName, varName, [minMaxInit, minMaxLead, minMaxY, minMaxX])


def readTotal4d(modelName, varName, minMaxX, minMaxY, minMaxZ, minMaxLead, minMaxInit):
    if varName not in ['u', 'v', 't', 'q', 'z', 'vp', 'sf']:
        raise ValueError(f' unrecognized varName "{varName}", try readTotal4d?')
    numDims = 4
    return readTotal(modelName, varName, [minMaxInit, minMaxLead, minMaxZ, minMaxY, minMaxX])


def readTotal(modelName, varName, minMaxs):
    numDims = len(minMaxs) - 1
    if numDims == 3:
        minMaxInit, minMaxLead, minMaxY, minMaxX = minMaxs
        minMaxZ = [-np.inf, np.inf]
    elif numDims == 4:
        minMaxInit, minMaxLead, minMaxZ, minMaxY, minMaxX = minMaxs

    minMaxInit = minMaxs[0]
    minMaxLead = minMaxs[1]
    numLeads = int(minMaxLead[1] - minMaxLead[0]) + 1
    numInits = int(minMaxInit[1] - minMaxInit[0]) + 1

    time = np.r_[minMaxInit[0]:minMaxInit[1]+1]
    lead = np.r_[minMaxLead[0]:minMaxLead[1]+1]
    nx, ny, nz, lon, lat, lev = getNxNyNz(minMaxX, minMaxY, minMaxZ)
    if numDims ==  3:
        varShape = (numInits, numLeads, ny, nx)
        dims = [time, lead, lat, lon]
    elif numDims == 4:
        varShape = (numInits, numLeads, nz, ny, nx)
        dims = [time, lead, lev, lat, lon]

    var = np.nan * np.ones(varShape)

    fileName = '/nwpr/gfs/com120/9_data/models/processed/{modelName}/' \
             + '{year:02d}/{month:02d}/{day:02d}z00/E000/global_1p0_{varName}.nc'
    
    ncVarName = varName_to_ncVarName(varName)

    fp = Fp()
    for iInit in range(numInits):
        fp.flushPrint(f' {iInit+1} / {numInits}')
        initDate = minMaxInit[0] + iInit
        year, month, day = tt.year(initDate), tt.month(initDate), tt.day(initDate)

        f = fileName.format(modelName=modelName, year=year, month=month, day=day, varName=varName)
        if not (os.path.isfile(f) or os.path.islink(f)):
            print(f'skipping missing file {f}')
            continue

        varSlice, *dimSlice = rt.readw2g(
            filename=f, 
            varName=ncVarName,
            minMaxs=minMaxs[1:],
            iDimT=0,
            minTime=0,
            intervalTime=[1,'day']
        )
        numLeadSlice = varSlice.shape[0]
        if numLeadSlice < numLeads:
            print(f'warning: lead is only {numLeadSlice} for {tt.float2format(initDate)} (inquired lead={numLeads})')
        var[iInit, 0:numLeadSlice, :] = varSlice
    fp.flushPrint('')

    return var, dims

def readModelClim(modelName, varName, minMaxs, climYears=[2011, 2020], climType='5dma'):
    minMaxs = deepcopy(minMaxs)
    numDims = len(minMaxs) - 1
    if numDims == 3:
        minMaxInit, minMaxLead, minMaxY, minMaxX = minMaxs
        minMaxZ = [-np.inf, np.inf]
    elif numDims == 4:
        minMaxInit, minMaxLead, minMaxZ, minMaxY, minMaxX = minMaxs

    minMaxInit = minMaxs[0]
    minMaxLead = minMaxs[1]
    numLeads = int(minMaxLead[1] - minMaxLead[0]) + 1
    numInits = int(minMaxInit[1] - minMaxInit[0]) + 1

    # force the year to be 2000 for reading climatology
    minMaxInit[0] = tt.ymd2float( 2000, tt.month(minMaxInit[0]), tt.day(minMaxInit[0]))
    minMaxInit[1] = tt.ymd2float( 2000, tt.month(minMaxInit[1]), tt.day(minMaxInit[1]))

    minMonth = tt.month(minMaxInit[0])
    maxMonth = tt.month(minMaxInit[1])    
    numMonths = maxMonth - minMonth + 1

    time = np.r_[minMaxInit[0]:minMaxInit[1]+1]
    lead = np.r_[minMaxLead[0]:minMaxLead[1]+1]
    nx, ny, nz, lon, lat, lev = getNxNyNz(minMaxX, minMaxY, minMaxZ)
    if numDims ==  3:
        varShape = (numInits, numLeads, ny, nx)
        dims = [time, lead, lat, lon]
    elif numDims == 4:
        varShape = (numInits, numLeads, nz, ny, nx)
        dims = [time, lead, lev, lat, lon]

    var = np.nan * np.ones(varShape)

    fileName = '/nwpr/gfs/com120/9_data/models/processed/{modelName}/clim/' \
             + '{varName}_mon{month:02d}_{climYearStart}_{climYearEnd}_1p0_{climType}.nc'

    for iMonth in range(numMonths):
        month = minMonth + iMonth

        f = fileName.format(
            modelName=modelName,
            varName=varName,
            month=month,
            climYearStart=climYears[0],
            climYearEnd=climYears[1],
            climType=climType,
        )

        if not (os.path.isfile(f) or os.path.islink(f)):
            raise FileNotFoundError(f'file name = {f}')
        
        varSlice, *dimSlice = rt.readw2g(
            filename=f, 
            varName=varName_to_ncVarName(varName),
            minMaxs=minMaxs,
            iDimT=0,
            minTime=tt.ymd2float(2000,month,1),
            intervalTime=[1,'day']
        )        
        numInitSlice = varSlice.shape[0]
        numLeadSlice = varSlice.shape[1]
        if numLeadSlice < numLeads:
            print(f'warning: numLead is only {numLeadSlice} for {month=} (inquired lead={numLeads})')

        iInitStart = np.where( np.array([ tt.month(t) for t in time]) == month)[0][0]
        var[iInitStart:numInitSlice, 0:numLeadSlice, :] = varSlice

    return var, dims

def readModelAnomaly(modelName, varName, minMaxs, climData, climYears=[2011, 2020], climType='5dma'):
    if varName in ['u', 'v', 't', 'q', 'z'] and len(minMaxs) != 5:
        raise ValueError('wrong numbers of minMaxs for 4d variable. (should be [[init], [lead], [lev], [lat], [lon]])')
    if varName in ['u10', 'v10', 't2m', 'prec', 'mslp', 'olr'] and len(minMaxs) != 4:
        raise ValueError('wrong numbers of minMaxs for 3d variable. (should be [[init], [lead], [lat], [lon]])')
    
    if climData == 'model':
        varClim, dimClim = readModelClim(modelName, varName, minMaxs, climYears, climType)
    elif climData == 'obs':
        minMaxX = minMaxs[-1]
        minMaxY = minMaxs[-2]
        minMaxZ = minMaxs[-3]
        minMaxT = minMaxs[0]

        # what a mess..
        if varName=='u' and minMaxZ == [20000, 20000]:
            varNameEra5 = 'u200'
        elif varName=='u' and minMaxZ == [85000, 85000]:
            varNameEra5 = 'u850'
        elif varName=='v' and minMaxZ == [20000, 20000]:
            varNameEra5 = 'v200'
        elif varName=='v' and minMaxZ == [85000, 85000]:
            varNameEra5 = 'v850'
        elif varName=='z' and minMaxZ == [50000, 50000]:
            varNameEra5 = 'z500'
        elif varName=='vp' and minMaxZ == [20000, 20000]:
            varNameEra5 = 'vp200'
        elif varName=='vp' and minMaxZ == [85000, 85000]:
            varNameEra5 = 'vp850'
        elif varName=='sf' and minMaxZ == [20000, 20000]:
            varNameEra5 = 'sf200'
        elif varName=='sf' and minMaxZ == [85000, 85000]:
            varNameEra5 = 'sf850'
        elif varName not in ['olr', 'prec']:
            raise ValueError(f'{varName=}, {minMaxZ=} is not implemented yet.')

        if varName in ['u', 'v', 'z', 'vp', 'sf']:
            varClim, dimClim = rt.era5_3dVar_clim_day_0p5(varNameEra5, minMaxX, minMaxY, minMaxT, climYears, climType)
        elif varName == 'olr':
            varClim, dimClim = rt.cbo_olr_clim_day_1p0( minMaxX, minMaxY, minMaxT, climYears, climType)
        elif varName == 'prec':
            varClim, dimClim = rt.cmorph_prec_clim_day_0p5( minMaxX, minMaxY, minMaxT, climYears, climType)

    else:
        raise ValueError(f'{climData=} is not implemented yet.')

    varTotal, dimTotal = readTotal(modelName, varName, minMaxs)

    if climData == 'obs': # then interpolation is needed
        lonClim, latClim = dimClim[-1], dimClim[-2]
        lonTotal, latTotal = dimTotal[-1], dimTotal[-2]
        varClim = interp_1d( lonClim, varClim, lonTotal, axis=-1, extrapolate=True)
        varClim = interp_1d( latClim, varClim, latTotal, axis=-2, extrapolate=True)
        varClim = np.tile(varClim, (1 for __ in range(len(minMaxs))))
        varClim = np.swapaxes(varClim, 0, -3)

    varAnomaly = calModelAnomaly(varTotal, dimTotal[0], varClim, dimClim[0])
    # print(f'{varTotal.shape=}')
    # print(f'{varClim.shape=}')
    # print(f'{varAnomaly.shape=}')
    return varAnomaly, dimTotal


def calModelAnomaly(varTotal, timeTotal, varClim, timeClim):
    timeClim = [tt.month(t) * 100 + tt.day(t) for t in timeClim]
    timeTotal = [tt.month(t) * 100 + tt.day(t) for t in timeTotal]
    iInitList = [timeClim.index(t) for t in timeTotal]
    return varTotal[0:len(timeTotal), :] - varClim[iInitList, :]


def varName_to_ncVarName(varName):
    if varName == 'vp':
        return 'velopot'
    elif varName == 'sf':
        return 'stream'
    else:
        return varName

if __name__ == '__main__':
    var, dims = readTotal4d(
        modelName='re_CWA_GEPSv2',
        varName='u',
        minMaxX=[100, 180],
        minMaxY=[-20, 20],
        minMaxLead=[0, 15],
        minMaxZ=[500_00, 1000_00],
        minMaxInit=[tt.ymd2float(2020,7,3), tt.ymd2float(2020,7,15)],
    )
    print(var.shape)

