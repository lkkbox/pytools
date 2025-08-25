from ..checktools import checkType
from ._shared import ModelClimFile, checkNDim
from .. import timetools as tt
from ..terminaltools import FlushPrinter
import numpy as np
import os


def readModelClim(
    modelName, dataType, varName, minMaxs, initTimes, members,
    climYears=[2001, 2020], climType='5dma', skipLeadCheck=True, warning=True,
    rootDir=''
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
        checkType(skipLeadCheck, bool, 'skipLeadCheck')
        checkType(rootDir, str, 'rootDir')

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

        if not checkNDim(dataType, varName, inquiredNDim=len(minMaxs)):
            return False

        if not os.path.exists(rootDir):
            raise FileNotFoundError(f'{rootDir=}')
        return True

    def checkFileDimensions():
        # 1. check skips
        # 2. check the consistency of spatial dimension shape
        # 3. check the consistency of spatial dimension values
        # 4. check the consistency of lead time values
        #      and get the max(NT) among files

        failureReturns = (False, None)
        # 0. flattent the list and get rid of skipped files for a lazier life
        files = [file for sublist in modelFiles
                 for file in sublist if not file.skip]

        # 1. check skips (len=0?)
        if not files:
            fp.print('[Fatal Error]: no valid files for reading')
            return failureReturns

        # 2. check the consistency of spatial dimension shape
        varShapes = [file.varShape for file in files]

        if len(files) == 1:  # skip consistency check if only 1 file
            return True, files[0].getDimValues(minMaxs)

        if isAnalysis:
            spatialShapes = varShapes.copy()
        else:  # remove the time dimension
            spatialShapes = [s[1:] for s in varShapes]

        iFile, inconsistent = next(
            ((i, True) for i, shape in enumerate(spatialShapes[1:], 1)
                if shape is not None and shape != spatialShapes[0]),
            (None, False)
        )
        if inconsistent:
            fp.print('[file1]')
            fp.print(files[0])
            fp.print('[file2]')
            fp.print(files[iFile])
            fp.print(
                '[Fatal Error]: dimension shapes of input files are insonsistent')
            return failureReturns

        # 3. check the consistency of spatial dimension values
        dimValues = [file.getDimValues(minMaxs) for file in files]

        if isAnalysis:
            spatialDimValues = dimValues.copy()
        else:  # remove the time dimension
            spatialDimValues = [v[1:] for v in dimValues]

        iFile, inconsistent = next(  # loop over dimensions (lev, lat, lon..)
            ((iFile, True) for iFile, dimVals in enumerate(spatialDimValues[1:], 1)
                if dimVals is not None and next((  # loop over dimension values (lon1, lon2, ..)
                    True for val, val0 in zip(dimVals, spatialDimValues[0])
                    if (val != val0).any()), False)
             ), (None, False))

        if inconsistent:
            fp.print('[file1]')
            fp.print(files[0])
            fp.print(spatialDimValues[0])
            fp.print('[file2]')
            fp.print(files[iFile])
            fp.print(spatialDimValues[iFile])
            fp.print('[Fatal Error]: spatial dimension values'
                     ' of input files are insonsistent')
            return failureReturns

        # 4. check the consistency of lead time values
        #      and get the max(NT) among files
        if isAnalysis:
            return True, spatialDimValues[0]

        leads = [dimVals[0] for dimVals in dimValues]
        iMaxLead = np.argmax([len(lead) for lead in leads])
        LEAD = dimValues[iMaxLead][0]

        if not skipLeadCheck:
            iFile, inconsistent = next(
                ((i, True) for i, lead in enumerate(leads)
                 if lead != LEAD[:len(lead)]),
                (None, False))

            if inconsistent:
                fp.print('[file1]')
                fp.print(files[iMaxLead])
                fp.print(LEAD)
                fp.print('[file2]')
                fp.print(files[iFile])
                fp.print(leads[iFile])
                fp.print('[Fatal Error]: lead values'
                         ' of input files are insonsistent')
                return failureReturns

        return True, [dimValues[iMaxLead][0], *spatialDimValues[0]]

    #
    # ---- input settings
    #
    fp = FlushPrinter()
    failureReturns = (None, None)
    isAnalysis = dataType == 'analysis'
    if not validateInputArgs():
        return failureReturns

    #
    # ---- file settings and checing
    #
    fp.flush('validating input arguments and files..')
    modelFiles = [
        [ModelClimFile(
            modelName,
            dataType,
            varName,
            initTime,
            member,
            warning,
            rootDir,
            climType,
            climYears,
        ) for initTime in initTimes]
        for member in members
    ]
    stat, dims = checkFileDimensions()
    if not stat:
        return failureReturns

    #
    # ---- initialize the output data
    #
    numInitTimes = len(initTimes)
    numMembers = len(members)
    dataShape = [numInitTimes, numMembers, *[len(dim) for dim in dims]]
    fp.flush(f'creating data with shape = {dataShape}..')
    data = np.nan * np.ones(dataShape)

    #
    # ---- Let's go!!
    #
    for iMember in range(numMembers):
        for iInitTime in range(numInitTimes):
            fp.flush(
                f'reading {varName} clim {iMember}/{numMembers}, {iInitTime}/{numInitTimes}')

            file = modelFiles[iMember][iInitTime]
            if file.skip:
                continue

            dataPart, __ = file.read(minMaxs)
            if dataPart is None:
                continue

            if isAnalysis:
                data[iInitTime, iMember, :] = dataPart
                continue

            numLeads = dataPart.shape[0]
            data[iInitTime, iMember, :numLeads, :] = dataPart

    # ---- fix mslp units :((
    if varName == 'mslp': # fix the mslp value/units :((
        fieldMean = np.nanmean(data, axis=(-1, -2))
        for i in range(numInitTimes):
            for j in range(numMembers):
                for k in range(numLeads):
                    if fieldMean[i, j, k] > 1000 * 50:
                        data[i, j, k, :, :] /= 100 # -> hPa
                    elif fieldMean[i, j, k] < 1000 / 50: # GEPSv3 correction :((
                        data[i, j, k, :, :] *= 100 # -> hPa

    return data, dims
