'''
read multiple netcdf files and concatenate the data
read(
    paths: str, varName: str, minMaxs: list[list],
    stackedAlong: int | "new" , iDimT: int = None, decodeTime=True
):
'''
from .. import nctools as nct
from .. import checktools as chkt
from .. import terminaltools as tmt
import numpy as np
import os
import traceback
from dataclasses import dataclass


@dataclass
class _File:
    path: str
    stat: bool = True

    def checkPathExists(self):
        if not os.path.exists(self.path):
            self.stat = False
        return self.stat

    def checkVariableExists(self, varName):
        if not self.stat:
            return
        nct._errorIfVariableNotExists(self.path, varName)



def read(
    paths, varName, minMaxs, iDimT=None, decodeTime=True,
    stackedAlong='new', ignoreDimNames=False, iDimValIgnored=[],
    allowMissingFile=False, allowVaryingDimLength=False,
):
    fp = tmt.FlushPrinter()
    #
    # ---- validations
    fp.flush('multi read: validating..')
    chkt.checkType(paths, list, 'paths')
    chkt.checkType(varName, str, 'varName')
    chkt.checkType(minMaxs, list, 'minMaxs')
    chkt.checkType(stackedAlong, [int, str], 'stackedAlong')
    chkt.checkType(iDimT, [int, None], 'iDimT')
    chkt.checkType(decodeTime, bool, 'decodeTime')
    chkt.checkType(ignoreDimNames, bool, 'ignoreDimNames')
    chkt.checkType(iDimValIgnored, list, 'ignoreDimNames')
    chkt.checkType(allowMissingFile, bool, 'allowMissingFile')

    for path in paths:
        chkt.checkType(path, str, 'path in paths')

    for minMax in minMaxs:
        chkt.checkType(minMax, [list], 'elements in minMaxs')
        if len(minMax) != 2:
            raise ValueError('The minMax in "minMaxs" must have 2 elements')
        for minOrMax in minMax:
            chkt.checkType(minOrMax, [int, float, None], 'min or max')

    if isinstance(stackedAlong, str) and stackedAlong != 'new':
        raise ValueError('"stackedAlong" can only be "new" or an integer')

    if not decodeTime and iDimT is not None:
        raise ValueError('"decodeTime" is false but "iDimT" is assigned.')

    if iDimT is not None:
        if not isinstance(iDimT, int):
            raise ValueError('"iDimT" must be None or an integer.')
           
    for ignoreDimValue in iDimValIgnored:
        chkt.checkType(ignoreDimValue, int, 'elements in iDimValIgnored')
    
    #
    # ---- check the files
    files = [_File(path) for path in paths]

    fp.flush('multi read: checking paths..')
    for file in files:
        stat = file.checkPathExists()
        if not stat:
            if not allowMissingFile:
                raise FileNotFoundError(f'{file.path=}')
            else:
                print(f'warning: path not found {file.path}')

    if allowMissingFile and not any([file.stat for file in files]):
        raise FileNotFoundError(f'all paths not found {paths[0]} and more...')

    fp.flush('multi read: checking variable name..')
    for file in files:
        if not file.stat:
            continue
        nct._errorIfVariableNotExists(file.path, varName)

    fp.flush('multi read: checking dimension names..')
    dimNames = None
    if not ignoreDimNames:  # check dim names
        for file in files:
            if not file.stat:
                continue
            thisDimNames = nct.getDimNames(file.path, varName)
            if dimNames is None:
                dimNames = thisDimNames
            elif dimNames != thisDimNames:
                raise RuntimeError(
                    f'inconsistent dimNames: {dimNames} {thisDimNames} {path}'
                )
    elif ignoreDimNames: # get from 1 file only
        for file in files:
            if not file.stat:
                continue
            dimNames = nct.getDimNames(file.path, varName)
            break

    if dimNames is None:
        raise RuntimeError(f'unable to determine dimNames from paths={[f.path for f in files]}')

    fp.flush('multi read: checking minMaxs..')
    numDims = len(dimNames)
    # validate input minMaxs
    if len(minMaxs) != numDims:
        raise ValueError(f'{len(minMaxs)=} but {numDims=}')

    # determine the stack dimensions
    iDimStacks = list(range(numDims))
    if isinstance(stackedAlong, int):
        if (  # validate the value of stackedAlong
            stackedAlong >= numDims
            or stackedAlong < -numDims
        ):
            raise ValueError(f'{numDims=} but {stackedAlong=}')
        iDimStacks.pop(stackedAlong)

    fp.flush('multi read: checking dimension values..')
    # check shapes
    varShape = None
    for file in files:
        if not file.stat:
            continue
        thisVarShape = list(nct.getVarShape(file.path, varName))
        thisStackedShape = [thisVarShape[i] for i in iDimStacks]
        if varShape is None:
            varShape = thisVarShape.copy()
            stackedShape = thisStackedShape

        if not allowVaryingDimLength and stackedShape != thisStackedShape:
            raise RuntimeError(
                f'inconsistent varShape: {varShape} {thisVarShape} for {stackedAlong=} {path}, {paths[0]}'
            )
        elif len(stackedShape) != len(thisStackedShape):
            raise RuntimeError(
                f'inconsistent len(varShape): {varShape} {thisVarShape} for {stackedAlong=} {path}, {paths[0]}'
            )
        else:
            stackedShape = [max([l1, l2]) for l1, l2 in zip(stackedShape, thisStackedShape)]
        
    # check and get the stacked dimValues
    dimVals, dims = None, None
    for file in files:
        if file.stat:
            thisDimVals = []
            local_dimNames = nct.getDimNames(file.path, varName)
            for i in range(numDims):
                dimIsTime = local_dimNames[i] in [
                    'time', 'valid_time',
                    *[f'time{i}' for i in range(10)],
                    *[f'time_{i}' for i in range(10)],
                ]
                try:
                    __, (dim,) = nct.ncreadByDimRange(
                        file.path, local_dimNames[i], [minMaxs[i]], decodeTime=dimIsTime
                    )
                except:
                    traceback.print_exc()
                    raise RuntimeError(f'{path=}, dimName={local_dimNames[i]}, minMax={minMaxs[i]}')
                thisDimVals.append(dim)

            # check the dimvalues
            if dimVals is None:
                dimVals = thisDimVals
            else:
                for idim, (d1, d2) in enumerate(zip(dimVals, thisDimVals)):
                    if idim in iDimValIgnored or idim == stackedAlong:
                        continue
                    if not np.array_equal(d1, d2):
                        print([d1, d2])
                        raise RuntimeError(
                            f'inconsistent dim values: {idim=} for {paths[0]}, {path}'
                        )
                
        # assign the output dim values
        if dims is None:
            if stackedAlong == 'new':
                dims = [list(range(len(paths))), *dimVals]
            else:
                dims = dimVals
        elif stackedAlong != 'new':
            if file.stat:
                stackedDim = thisDimVals[stackedAlong]
            else:
                stackedDim = np.nan
            dims[stackedAlong] = np.concatenate((dims[stackedAlong], stackedDim))

    dataShape = [len(d) for d in dims]

    data = np.nan * np.ones((dataShape))
    if stackedAlong != 'new': # shift operation to idim = 0
        data = np.swapaxes(data, 0, stackedAlong)

    sliceStart, sliceEnd = 0, 0
    numFiles = len(files)
    for iFile, file in enumerate(files):
        fp.flush(f'multi reading {iFile}/{numFiles}..')
        if not file.stat:
            sliceEnd += 1
            sliceStart += 1
            continue

        thisData, __ = nct.ncreadByDimRange( # read
            file.path, varName, minMaxs, iDimT, decodeTime
        )
        if stackedAlong != 'new':
            thisData = np.swapaxes(thisData, 0, stackedAlong)
            thisRecordLen = thisData.shape[0]
        elif stackedAlong == 'new':
            thisRecordLen = 1

        sliceEnd += thisRecordLen
        if data.ndim == 1:
            data[slice(sliceStart, sliceEnd)] = thisData
        else:
            data[slice(sliceStart, sliceEnd), :] = thisData

        sliceStart += thisRecordLen

    fp.flush(f'')
        
    if stackedAlong != 'new':
        data = np.swapaxes(data, 0, stackedAlong)

    return data, dims
    


def test():
    print('test read 1')
    data, dims = read(
        [
            '/nwpr/gfs/com120/9_data/ERA5/daymean/PRS/u/ERA5_u_201801_r720x360_1day.nc',
            '/nwpr/gfs/com120/9_data/ERA5/daymean/PRS/u/ERA5_u_201802_r720x360_1day.nc',
            '/nwpr/gfs/com120/9_data/ERA5/daymean/PRS/u/ERA5_u_201803_r720x360_1day.nc',
        ],
        'u', [[None, None], [850, 925], [-15, 15], [120, 150]], stackedAlong=0,
    )
    print(f'{data.shape = }')
    print(f'{np.mean(data) = }')

    data, dims = read(
        [
            '/nwpr/gfs/com120/9_data/ERA5/q_budget/raw/u/2001/ERA5_u_20010201_tropIoPo_3hr.nc',
            '/nwpr/gfs/com120/9_data/ERA5/q_budget/raw/u/2001/ERA5_u_20010202_tropIoPo_3hr.nc',
            '/nwpr/gfs/com120/9_data/ERA5/q_budget/raw/u/2001/ERA5_u_20010203_tropIoPo_3hr.nc',
        ],
        'u', [[None, None], [850, 925], [-15, 15], [120, 140]], stackedAlong=0, iDimValIgnored=[0]
    )
    print(f'{data.shape = }')
    print(f'{np.mean(data) = }')
    # print(dims)

    data, dims = read(
        [
            '/nwpr/gfs/com120/9_data/models/processed/re_GEPSv3_CFSR/2013/01/07z00/E000/analysis_u.nc',
            '/nwpr/gfs/com120/9_data/models/processed/re_GEPSv3_CFSR/2013/01/08z00/E000/analysis_u.nc',
        ],
        'u', [[850_00, 925_00], [-15, 15], [120, 125]], stackedAlong=-1, ignoreDimNames=True, decodeTime=False
    )
    print(f'{data.shape = }')
    print(f'{np.mean(data) = }')
    print(dims)
    print('passed.')
