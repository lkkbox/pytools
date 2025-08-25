from ..checktools import checkType
from ._shared import checkNDim
from .readModelClim import readModelClim
from .readTotal import readTotal
from .. import timetools as tt
from ..terminaltools import FlushPrinter
from ..caltools import interp_1d, conform_axis
import numpy as np
import os


def readAnomaly(
    modelName, dataType, varName, minMaxs, initTimes, members,
    climYears=[2001, 2020], climType='5dma', climData='model',
    skipLeadCheck=True, warning=True, rootDir='/nwpr/gfs/com120/9_data/models/processed',
):
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
    climData = 'model' or 'obs'

    -> var = var[member, init, lead, (z,), y, x]
    -> dims = [member, init, lead, (z,), y, x]
    '''
    def validateInputArgs():
        checkType(modelName, str, 'modelName')
        checkType(dataType, str, 'dataType')
        checkType(varName, str, 'varName')
        checkType(minMaxs, list, 'minMaxs')
        checkType(initTimes, list, 'initTimes')
        checkType(members, list, 'members')
        checkType(climYears, [list, tuple], 'climYears')
        checkType(climType, str, 'climType')
        checkType(climData, str, 'climData')
        checkType(skipLeadCheck, bool, 'skipLeadCheck')
        checkType(rootDir, str, 'rootDir')

        if not os.path.exists(rootDir):
            raise FileNotFoundError(f'{rootDir=}')

        for e in initTimes:
            checkType(e, [float, int], 'element in initTimes')
        for e in members:
            checkType(e, int, 'element in members')
        for sublist in minMaxs:
            checkType(sublist, list, 'sublists in minMaxs')
            if len(sublist) != 2:
                raise ValueError('each minMax pair must be 2 elements')
            for e in sublist:
                checkType(e, [float, int, None], 'elements in minMaxs')
        if climData not in ['model']:
            raise ValueError('climData must be "model".')

        if not checkNDim(dataType, varName, inquiredNDim=len(minMaxs)):
            return False
        return True

    #
    # ---- input settings
    #
    failureReturns = (None, None)
    if not validateInputArgs():
        return failureReturns
    
    #
    # ---- find unique initTimes for reading climatology
    #
    initMmdds = [tt.float2format(initTime, '%m%d') for initTime in initTimes]
    climMmdds = list(set(initMmdds))
    climTimes = [tt.ymd2float(2000, int(mmdd[:2]), int(mmdd[2:])) for mmdd in climMmdds]
    iClimDates = [climMmdds.index(initMmdd) for initMmdd in initMmdds]
    # # --- for checking the date indices are correct
    # print(f'initTimes             = {[tt.float2format(d) for d in initTimes]}')
    # print(f'climTimes[iClimDates] = {[tt.float2format(climTimes[iClimDate]) for iClimDate in iClimDates]}')
    # print(f'climTimes = {[tt.float2format(d) for d in climTimes]}')
    # print(f'{iClimDates = }')

    #
    # ---- read clim and total data
    #
    dataClim, dimsClim = readModelClim(
        modelName, dataType, varName, minMaxs, climTimes, 
        members, climYears, climType, skipLeadCheck, warning,
        rootDir
    )
    if dataClim is None:
        print('[Fatal Error] climate data is not read')
        return failureReturns
    
    dataTotal, dimsTotal = readTotal(
        modelName, dataType, varName, minMaxs, initTimes, members, skipLeadCheck, warning,
        rootDir,
    )
    if dataTotal is None:
        print('[Fatal Error] total data is not read')
        return failureReturns

    #
    # ---- interpolate if needed
    lonClim, latClim = dimsClim[-1], dimsClim[-2]
    lonTotal, latTotal = dimsTotal[-1], dimsTotal[-2]
    if not np.array_equal(lonClim, lonTotal):
        interp_1d(lonClim, dataClim, lonTotal, axis=-1, extrapolate=True)
    if not np.array_equal(latClim, latTotal):
        interp_1d(latClim, dataClim, latTotal, axis=-2, extrapolate=True)

    #
    # ---- subtract the climatology from total
    #
    if dataTotal.ndim == 5:
        dataAnomaly = dataTotal - dataClim[iClimDates, :, :dataTotal.shape[2], :, :] # for smaller numLeads to work
    elif dataTotal.ndim == 6:
        dataTotal, dataClim, dims = conform_axis(dataTotal, dataClim, dimsTotal, dimsClim, -3)
        dimsTotal = dims
        dimsClim = dims
        dataAnomaly = dataTotal - dataClim[iClimDates, :, :dataTotal.shape[2], :, :, :] # for smaller numLeads to work
    else:
        raise RuntimeError(f'what the shape???? {dataTotal.shape = }')
    return dataAnomaly, dimsTotal

   
