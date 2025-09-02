'''
2024/12
This is a module for reading the processed model data
'''
from ..caltools import interp_1d
from ..plottools import FlushPrinter as Fp
from .. import timetools as tt
from ..readtools.readtools import readw2g
from ..readtools.era5_prs import readClim as _readObsPrsClim
from ..readtools.era5_sfc import readClim as _readObsSfcClim
from ..readtools.cmorph_precip import cmorph_prec_clim_day_0p5 as _readObsPrecClim
from ..readtools.cbo_olr import cbo_olr_clim_day_1p0 as _readObsOlrClim
import numpy as np
import os


def example():
    modelName = 're_GEPSv3_CFSR'
    varName = 'u'
    initList = []  # list of initialize date
    minMaxs = [   # along the dimension order of the nc file
        [0, 50],            # dimension lead (days)
        [200_00, 200_00],   # (optional): dimension z (Pa)
        [-15, 15],          # dimension lat
        [100, 120],         # dimension lon
    ]
    memberList = [0]  # list of ensemble members

    climYears = [2001, 2020]
    climType = '5dma'  # 5dma for 5day average

    # ===== settings end ==== #

    for varName in ['u', 'olr']:
        for initList in [
            [tt.ymd2float(2018, 1, 3)],
        ]:
            
            if varName == 'u':
                thisMinMaxs = minMaxs
            else:
                thisMinMaxs = [minMaxs[i] for i in [0, 2, 3]]

            var, dims = readTotal(
                modelName, varName, thisMinMaxs, initList, memberList
            )

            var, dims = readModelClim(
                modelName, varName, thisMinMaxs, initList, memberList,
                climYears, climType
            )

            var, dims = readModelAnomaly(
                modelName, varName, thisMinMaxs, initList, memberList,
                climYears, climType, climData='model'
            )
            
            var, dims = readModelAnomaly(
                modelName, varName, thisMinMaxs, initList, memberList,
                climYears, climType, climData='obs'
            )

            var, dims, __ = readTotalBiasCorrected(
                modelName, varName, thisMinMaxs, initList, memberList,
                climYears, climType,
            )

def readTotal(modelName, varName, minMaxs, initList, memberList):
    '''
    minMaxs = [
        minMaxLead,
        (minMaxZ,)
        minMaxY,
        minMaxX,
    ]
    -> var = var[member, init, lead, (z,), y, x]
    -> dims = [member, init, lead, (z,), y, x]
    '''
    def getFileName():
        year, month = tt.year(initDate), tt.month(initDate)
        day, hour = tt.day(initDate), tt.hour(initDate)
        return f'{_getRootDir()}/' \
            + f'{modelName}/{year:02d}/{month:02d}/{day:02d}z{hour:02d}/' \
            + f'E{member:03d}/global_daily_1p0_{varName}.nc'

    def getStrThisFile():
        return f'{tt.float2format(initDate, '%Y%m%d_%H')} ' \
            f'mem{member} {varName} {modelName}'

    def read():
        fileName = getFileName()

        if not _checkFileExistence(fp, fileName, strThisFile):
            return

        result = _read(fileName, ncVarName, minMaxs)
        return result

    _checkMinMaxs(varName, minMaxs)
    numDims = len(minMaxs)
    numInits = len(initList)
    numMembers = len(memberList)

    minMaxLead = minMaxs[0]
    leadList = np.r_[minMaxLead[0] : minMaxLead[1]+1]
    numLeads = len(leadList)
    

    isInitilized, var, dims = False, None, None

    ncVarName = _varName_to_ncVarName(varName)

    fp = Fp()
    for iInit, initDate in enumerate(initList):
        for iMember, member in enumerate(memberList):

            fp.flushPrint(
                f' ({iInit+1}/{numInits}) ({iMember+1}/{numMembers})')

            strThisFile = getStrThisFile()
            result = read()
            if result is None:
                continue
            varSlice, dimSlice = result

            numLeadSlice = varSlice.shape[0]
            if numLeadSlice < numLeads:
                _printWarningNumLead(fp, numLeads, numLeadSlice, strThisFile)

            if not isInitilized:
                var, dims = _initilizeOutput(
                    dimSlice, numMembers, numInits, numDims, leadList
                )
                isInitilized = True

            var[iMember, iInit, :numLeadSlice, :] = varSlice
    fp.flushPrint('')
    return var, dims


def readModelClim(modelName, varName, minMaxs, initList, memberList,
                  climYears=[2006, 2020], climType='5dma'):
    '''
    minMaxs = [
        minMaxLead,
        (minMaxZ,)
        minMaxY,
        minMaxX,
    ]

    climYears = [yearBegin, yearEnd]

    climType = '1day', '5dma', or '3harm
        1day = raw daily climate
        5dma = 5-day moving average of 1day
        3harm = first 3 annual harmonics of 5dma

    -> var = var[member, init, lead, (z,), y, x]
    -> dims = [member, init, lead, (z,), y, x]
    '''
    def getFileName():
        strClimYears = '_'.join([str(y) for y in climYears])
        return f'{_getRootDir()}/{modelName}/clim/E{member:03d}/' \
            f'{varName}_mon{initMonth:02d}_{strClimYears}' \
            f'_1p0_{climType}.nc'

    def read():
        fileName = getFileName()

        if not _checkFileExistence(fp, fileName, strThisFile):
            return

        result = _read(fileName, ncVarName, [minMaxInit, *minMaxs])
        return result

    _checkMinMaxs(varName, minMaxs)

    minMaxLead = minMaxs[0]
    leadList = np.r_[minMaxLead[0] : minMaxLead[1]+1]

    numInits = len(initList)
    numLeads = len(leadList)    
    numDims = len(minMaxs)
    numMembers = len(memberList)

    # force init to be in year 2000, and hour = 00z
    initList = [tt.ymd2float(
        2000, tt.month(i), tt.day(i)
    ) for i in initList]

    # get the months (file stratified by months)
    initMonthList = [tt.month(i) for i in initList]
    uniqueInitMonthList = list(set(initMonthList))
    numUniqueInitMonths = len(uniqueInitMonthList)

    isInitilized, var, dims = False, None, None

    ncVarName = _varName_to_ncVarName(varName)

    fp = Fp()
    for iInitMonth, initMonth in enumerate(initMonthList):
        for iMember, member in enumerate(memberList):

            fp.flushPrint(
                f' ({iInitMonth+1}/{numUniqueInitMonths}) ({iMember+1}/{numMembers})')

            strThisFile = f'clim mon{initMonth} ' + \
                f'mem{member} {varName} {modelName}'

            initsRequest = [i for i, m in zip(
                initList, initMonthList) if m == initMonth]
            minMaxInit = [min(initsRequest), max(initsRequest)]

            result = read()
            if result is None:
                continue

            varSlice, dimSlice = result

            numLeadSlice = varSlice.shape[1]
            if numLeadSlice < numLeads:
                _printWarningNumLead(fp, numLeads, numLeadSlice, strThisFile)

            if not isInitilized:
                var, dims = _initilizeOutput(
                    dimSlice, numMembers, numInits, numDims, leadList
                )
                isInitilized = True

            initsRead = dimSlice[0]
            iInits = [initsRequest.index(tt.dayOfClim(float(i)))
                      for i in initsRead]

            var[iMember, iInits, :numLeadSlice, :] = varSlice
    fp.flushPrint('')
    return var, dims


def readModelAnomaly(
        modelName, varName, minMaxs, initList, memberList,
        climYears=[2006, 2020], climType='5dma', climData='model'
):
   
    if climData not in ['model', 'obs']:
        raise ValueError(f'{climData=} is not implemented yet')

    # ---- read clim ---- #
    if climData == 'model':
        varClim, dimClim = readModelClim(
            modelName, varName, minMaxs, initList,
            memberList, climYears, climType
        )

    elif climData == 'obs':
        varClim, dimClim = _readObsClim(
            minMaxs, initList, varName, climYears, climType
        )

    if varClim is None:
        print('ERROR: failed to read climate data')
        return None, None

    # ---- read total ---- #
    varTotal, dimTotal = readTotal(
        modelName, varName, minMaxs, initList, memberList
    )
    if varTotal is None:
        print('ERROR: failed to read model total data')
        return None, None

    # ---- interpolation ---- #
    lonClim, latClim = dimClim[-1], dimClim[-2]
    lonTotal, latTotal = dimTotal[-1], dimTotal[-2]
    varClim = interp_1d(lonClim, varClim, lonTotal,
                        axis=-1, extrapolate=True)
    varClim = interp_1d(latClim, varClim, latTotal,
                        axis=-2, extrapolate=True)
    
    # ---- interpolate and subtract the climatology ---- #
    if climData == 'obs': 
        # subtraction
        leads = dimTotal[0]
        timeClim = dimClim[0]
        timeClim = [tt.dayOfClim(t) for t in timeClim]
        varAnomaly = varTotal
        varClim = np.tile(varClim, (1 for __ in range(varTotal.ndim)))
        for iInit, init in enumerate(initList):
            for iLead, lead in enumerate(leads):
                valid = tt.dayOfClim(float(np.floor(init + lead)))
                iClim = timeClim.index(valid)
                varAnomaly[:, iInit, iLead, :] -= np.squeeze(varClim[:, :, iClim, :])

    elif climData == 'model':
        varAnomaly = varTotal - varClim

    return varAnomaly, dimTotal


def readTotalBiasCorrected(
        modelName, varName, minMaxs, initList, memberList,
        climYears=[2006, 2020], climType='5dma',
):
    varAnomaly, dimAnomaly = readModelAnomaly(
        modelName, varName, minMaxs, initList, memberList,
        climYears, climType, climData='model'
    )
    varClim, dimClim = _readObsClim(
        minMaxs, initList, varName, climYears, climType
    )
    
    # interpolation
    lonClim, latClim = dimClim[-1], dimClim[-2]
    lonAnomaly, latAnomaly = dimAnomaly[-1], dimAnomaly[-2]
    varClim = interp_1d(lonClim, varClim, lonAnomaly,
                        axis=-1, extrapolate=True)
    varClim = interp_1d(latClim, varClim, latAnomaly,
                        axis=-2, extrapolate=True)
    # subtraction
    leads = dimAnomaly[0]
    timeClim = dimClim[0]
    timeClim = [tt.dayOfClim(t) for t in timeClim]
    varTotal = varAnomaly
    varClim = np.tile(varClim, (1 for __ in range(varTotal.ndim)))
    for iInit, init in enumerate(initList):
        for iLead, lead in enumerate(leads):
            valid = tt.dayOfClim(float(np.floor(init + lead)))
            iClim = timeClim.index(valid)
            varTotal[:, iInit, iLead, :] += np.squeeze(varClim[:, :, iClim, :])

    return varTotal, dimAnomaly, varAnomaly
    
def _varName_to_ncVarName(varName):
    if varName == 'vp':
        return 'velopot'
    elif varName == 'sf':
        return 'stream'
    else:
        return varName


def _getRootDir():
    return '/nwpr/gfs/com120/9_data/models/processed'


def _checkFileExistence(fp, fileName, strThisFile):
    if not (os.path.isfile(fileName) or os.path.islink(fileName)):
        fp.flushPrint('')
        print(f'skipping missing file {strThisFile} ({fileName})')
        return False
    return True


def _read(fileName, ncVarName, minMaxs):
    varSlice, *dimSlice = readw2g(
        filename=fileName,
        varName=ncVarName,
        minMaxs=minMaxs,
        iDimT=0,
        minTime=0,
        intervalTime=[1, 'day']
    )
    return (varSlice, dimSlice)


def _printWarningNumLead(fp, numLeads, numLeadSlice, strThisFile):
    fp.flushPrint('')
    print(f'warning: numLeads retrieved={numLeadSlice} '
          f'inquired={numLeads} '
          f'for {strThisFile}'
          )


def _initilizeOutput(dimSlice, numMembers, numInits, numDims, lead):

    lon, lat = dimSlice[-1], dimSlice[-2]
    nx, ny, numLeads = len(lon), len(lat), len(lead)

    if numDims == 3:
        varShape = (numMembers, numInits, numLeads, ny, nx)
        dims = [lead, lat, lon]

    elif numDims == 4:
        lev = dimSlice[-3]
        nz = len(lev)
        varShape = (numMembers, numInits, numLeads, nz, ny, nx)
        dims = [lead, lev, lat, lon]

    var = np.nan * np.ones(varShape)
    return var, dims


def _checkMinMaxs(varName, minMaxs):
    varNames4d = ['u', 'v', 't', 'q', 'r', 'z', 'vp', 'sf']
    if varName in varNames4d and len(minMaxs) != 4:
        raise ValueError(f'wrong numbers ({len(minMaxs)}) '
                         f'of minMaxs for 4d variable "{varName}".'
                         ' (should be [lead, lev, lat, lon])')
    elif varName not in varNames4d and len(minMaxs) != 3:
        raise ValueError(f'wrong numbers ({len(minMaxs)}) '
                         f'of minMaxs for 3d variable "{varName}".'
                         '(should be [lead, lat, lon])')


def _readObsClim(minMaxs, initList, varName, climYears, climType):
    minMaxX = minMaxs[-1]
    minMaxY = minMaxs[-2]
    minMaxZ = [z/100 for z in minMaxs[-3]] # Pa -> hPa
    minMaxLead = minMaxs[0]
    minMaxInit = [min(initList), max(initList)]
    minMaxT = [i + l for i, l in zip(minMaxInit, minMaxLead)]

    if varName in ['u', 'v', 't', 'q', 'z']:
        varClim, dimClim = _readObsPrsClim(
            varName, minMaxX, minMaxY, minMaxZ, minMaxT, climYears, climType)

    elif varName in ['u10', 'v10', 't2m', 'pw', 'mslp']:
        varClim, dimClim = _readObsSfcClim(
            varName, minMaxX, minMaxY, minMaxT, climYears, climType)

    elif varName == 'olr':
        varClim, dimClim = _readObsOlrClim(
            minMaxX, minMaxY, minMaxT, climYears, climType)

    elif varName == 'prec':
        varClim, dimClim = _readObsPrecClim(
            minMaxX, minMaxY, minMaxT, climYears, climType)
    
    return varClim, dimClim