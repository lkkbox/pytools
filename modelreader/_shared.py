from ..nctools import getVarNames, getVarShape, ncreadByDimRange, getDimNames
from .. import timetools as tt
from dataclasses import dataclass, field
import os


def checkNDim(dataType, varName, inquiredNDim):
    validNDim, validDimName = _getValidNDims(dataType, varName)
    if inquiredNDim == validNDim:
        return True

    print(f'The numbers ({inquiredNDim}) of dimensions inquired'
          f' inquired for the variable "{varName}" '
          f'is wrong. (should be {validDimName})')
    return False


def _getValidNDims(dataType, varName):
    varNames4d = ['u', 'v', 'w', 't', 'q', 'r', 'z', 'vp', 'sf', 'uqx', 'vqy', 'wqp']
    varNames3d = ['u10', 'v10', 't2m', 'pw', 'mslp', 'olr', 'prec']
    varNames1d = ['lon', 'lat', 'plev', 'lev', 'lead', 'time']

    is1d = varName in varNames1d
    is3d = varName in varNames3d
    is4d = varName in varNames4d
    isAnalysis = dataType == 'analysis'

    if is1d:
        ndim, dimName = 1, varName
    elif isAnalysis and is3d:
        ndim, dimName = 2, 'lat, lon'
    elif isAnalysis and is4d:
        ndim, dimName = 3, 'lev, lat, lon'
    elif not isAnalysis and is3d:
        ndim, dimName = 3, 'lead, lat, lon'
    elif not isAnalysis and is4d:
        ndim, dimName = 4, 'lead, lev, lat, lon'
    else:
        print(f'warning: unrecognized varName = "{varName}"'
              ', assumed it to be a 3d variable')
        if isAnalysis:
            ndim, dimName = 2, 'lat, lon'
        else:
            ndim, dimName = 3, 'lead, lat, lon'
    return ndim, dimName


@dataclass
class ModelFileParent:
    modelName: str
    dataType: str
    varName: str
    initTime: float
    member: int
    warning: bool

    rootDir: str = ''
    varShape: any = field(init=False)
    path: str = field(init=False)
    skip: bool = field(init=False)

    def __post_init__(s):
        s.postInit()
    
    def postInit(s):
        s.ncVarName = s.varName
        s.check()
        if not rootDir:
            rootDir = '/nwpr/gfs/com120/9_data/models/processed'
    
    def check(s):
        s.getPath()
        s.skip = False
        s.skip = s._checkFileExists()
        s.skip = s._checkVarName()
        s.varShape = s._getVarShape()
    
    def getPath(s):
        s.path = tt.float2format(
            s.initTime,
            f'{s.rootDir}/{s.modelName}/%Y/%m/%dz%H/'
            f'E{s.member:03d}/{s.dataType}_{s.varName}.nc'
        )

    def read(s, minMaxs):
        if s.skip:
            return None, None

        data, dims = ncreadByDimRange(
            s.path, s.ncVarName, s._minMaxsLead2Valid(minMaxs),
            decodeTime=(s.dataType != 'analysis')
        )
        return data, dims


    def getDimValues(s, minMaxs):
        if s.skip:
            return None

        dimValues = []
        for (minMax, dimName) in zip(minMaxs, getDimNames(s.path, s.ncVarName)):
            dimValues.append(s._readDimValue(dimName, minMax))

        return dimValues

    def _readDimValue(s, dimName, minMax):
        if dimName.lower() == 'time':
            decodeTime = True
            dimRange = [
                lead + s.initTime if lead is not None else None for lead in minMax 
            ]
        else:
            decodeTime = False
            dimRange = minMax
        
        __, dimValue = ncreadByDimRange(
            s.path, dimName, [dimRange], decodeTime=decodeTime
        )
        dimValue = dimValue[0]

        if dimName.lower() == 'time':  # translate valid to lead for consistency
            dimValue = [valid - s.initTime for valid in dimValue]
        return dimValue

    def _checkFileExists(s):
        if s.skip:
            return True

        if os.path.exists(s.path):
            return False

        if s.warning:
            print(f'[warning] file not found: {s.path}', flush=True)
        return True

    def _checkVarName(s):
        if s.skip:
            return True

        if s.ncVarName in getVarNames(s.path):
            return False

        if s.warning:
            print(f'[warning] varName "{s.ncVarName}" not found in {s.path}')
        return True

    def _getVarShape(s):
        if s.skip:
            return None
        return getVarShape(s.path, s.ncVarName)

    def _minMaxsLead2Valid(s, minMaxsLead):
        minMaxsValid = minMaxsLead.copy()
        if s.dataType == 'analysis':
            return minMaxsValid
        minMaxsValid[0]= [
            lead + s.initTime if lead is not None else None for lead in minMaxsLead[0]
        ]
        return minMaxsValid
    

@dataclass
class ModelFile(ModelFileParent):
    ncVarName: str = None

    def postInit(s):
        if s.ncVarName is None:
            s.ncVarName = s.varName
        s.check()
    
    def getPath(s):
        s.path = tt.float2format(
            s.initTime,
            f'{s.rootDir}/{s.modelName}/%Y/%m/%dz%H/'
            f'E{s.member:03d}/{s.dataType}_{s.varName}.nc'
        )
    

@dataclass
class ModelClimFile(ModelFileParent):
    climType: str = '5dma'
    climYears: tuple = (2001, 2020)
    ncVarName: str = None

    def postInit(s):
        if s.ncVarName is None:
            s.ncVarName = s.varName
        s.check()

    def getPath(s):
        s.path = tt.float2format(
            s.initTime,
            f'{s.rootDir}/{s.modelName}/clim/E{s.member:03d}/{s.climType}/'
            f'{s.varName}/{s.dataType}_{s.varName}_%m%d_'
            f'{'_'.join([str(y) for y in s.climYears])}_{s.climType}.nc'
        )

    def read(s, minMaxs):
        if s.skip:
            return None, None

        data, dims = ncreadByDimRange(
            s.path, s.ncVarName, minMaxs, decodeTime=False
        )
        return data, dims
