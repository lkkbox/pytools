from .readTotal import readTotal
from .readModelClim import readModelClim
from .readAnomaly import readAnomaly
from .. import timetools as tt
from .. import nctools as nct
from ..caltools import interp_1d
import numpy as np


def example_readModelClim_ln23():
    modelName = 're_GEPSv3_CFSR'
    dataType = 'global_daily_1p0'
    varName = 'u'
    minMaxs = [
        [0, 10],
        [850_00, 850_00],
        [10, 20],
        [100, 120],
    ]
    initTimes = [
        tt.ymd2float(2020, 1, 1) + i for i in range(30)
    ]
    members = [0]

    var, dims = readTotal(modelName, dataType, varName,
                          minMaxs, initTimes, members)
    print(var.shape)
    print(dims)

    print('example passed.')


def example_readTotal_ln16():
    modelName = 'CWA_GEPSv2'
    dataType = 'global_daily_1p0'
    varName = 'u'
    minMaxs = [
        [0, 10],
        [850_00, 850_00],
        [10, 20],
        [100, 120],
    ]
    initTimes = [
        tt.ymd2float(2025, 1, 15, 0),
        tt.ymd2float(2025, 1, 16, 0),
    ]
    members = [0]

    var, dims = readTotal(modelName, dataType, varName,
                          minMaxs, initTimes, members)

    if var is None:
        print('result: no data is read.')
        return

    print(f'{[tt.float2format(t, '%Y-%m-%d %Hz') for t in initTimes]}')
    print(var.shape)
    print([len(d) for d in dims])

    print('result: passed.')


def example_readTotal_ln23():
    modelName = 're_GEPSv3_CFSR'
    dataType = 'global_daily_1p0'
    varName = 'u'
    minMaxs = [
        [0, 10],
        [850_00, 850_00],
        [10, 20],
        [100, 120],
    ]
    initTimes = [
        tt.ymd2float(2020, 1, 1) + i for i in range(30)
    ]
    members = [0]

    var, dims = readTotal(modelName, dataType, varName,
                          minMaxs, initTimes, members)
    print(var.shape)
    print(dims)

    print('example passed.')


def test_readTotal():
    def test(varName, minMaxs):
        dataNew, dims = readTotal(
            modelName=model,
            dataType=dataType,
            varName=varName,
            minMaxs=minMaxs,
            initTimes=initTimes,
            members=[0],
        )
        dataNew = np.squeeze(dataNew, axis=1)  # pop away member

        dataStupid, dims = stupidReadTotal(
            model=model,
            dataType=dataType,
            varName=varName,
            initTimes=initTimes,
            minMaxs=minMaxs,
        )
        return np.array_equiv(dataNew, dataStupid)

    initTimes = [
        tt.format2float(d, '%Y-%m-%d') for d in [
            '2003-01-07',
            '2015-01-12',
            '2005-07-12',
            '2017-01-12',
        ]
    ]
    dataType = 'global_daily_1p0'
    model = 're_GEPSv3_CFSR'
    # ---- 3d ---- #
    for testName, varName, minMaxs in zip(
        ['3d', '3d', '4d'],
        ['t2m', 'u10', 'u'],
        [
            [[0, 44],
             [-15, 15],
             [160, 180],],
            [[0, 44],
             [-15, 15],
             [160, 180],],
            [[0, 44],
             [850_00, 850_00],
             [-15, 15],
             [160, 180],],
        ]
    ):
        if test(varName, minMaxs):
            print(f'{testName} - {varName} passed!')
        else:
            print(f'{testName} - {varName} failed.')


def test_readClim():
    def test(varName, minMaxs):
        dataNew, dims = readModelClim(
            modelName=model,
            dataType=dataType,
            varName=varName,
            minMaxs=minMaxs,
            initTimes=initTimes,
            members=[0],
            climYears=[2001, 2020],
            climType='1day'
        )
        dataNew = np.squeeze(dataNew, axis=1) # member

        dataStupid, dims = stupidReadClim(
            model=model,
            dataType=dataType,
            varName=varName,
            initTimes=initTimes,
            minMaxs=minMaxs,
            climYears=[2001, 2020],
            climType='1day'
        )

        return np.array_equiv(dataNew, dataStupid)

    initTimes = [
        tt.format2float(d, '%Y-%m-%d') for d in [
            '2003-01-08',
            '2015-01-12',
            '2017-01-13',
        ]
    ]
    dataType = 'global_daily_1p0'
    model = 're_GEPSv3_CFSR'
    # ---- 3d ---- #
    for testName, varName, minMaxs in zip(
        ['3d', '3d', '4d'],
        ['t2m', 'u10', 'u'],
        [
            [[0, 44],
             [-15, 15],
             [160, 180],],
            [[0, 44],
             [-15, 15],
             [160, 180],],
            [[0, 44],
             [850_00, 850_00],
             [-15, 15],
             [160, 180],],
        ]
    ):
        if test(varName, minMaxs):
            print(f'{testName} - {varName} passed!')
        else:
            print(f'{testName} - {varName} failed.')


def test_readAnomaly():
    def test(varName, minMaxs):
        dataNew, dimsNew = readAnomaly(
            modelName=model,
            dataType=dataType,
            varName=varName,
            minMaxs=minMaxs,
            initTimes=initTimes,
            members=[0],
            climYears=climYears,
            climType=climType,
            climData='model',
        )
        dataNew = np.squeeze(dataNew, axis=1) # pop away the member dim

        dataTotal, dimsTotal = stupidReadTotal(
            model, dataType, varName, initTimes, minMaxs
        )
        dataClim, dimsClim = stupidReadClim(
            model, dataType, varName, initTimes, minMaxs, climYears, climType
        )
        
        lonClim, latClim = dimsClim[-1], dimsClim[-2]
        lonTotal, latTotal = dimsTotal[-1], dimsTotal[-2]
        if not np.array_equal(lonClim, lonTotal):
            interp_1d(lonClim, dataClim, lonTotal, axis=-1, extrapolate=True)
        if not np.array_equal(latClim, latTotal):
            interp_1d(latClim, dataClim, latTotal, axis=-2, extrapolate=True)

        
        dataStupid = dataTotal - dataClim

        dataStupid = np.float32(dataStupid)
        dataNew    = np.float32(dataNew)
        return np.array_equal(dataNew, dataStupid)
    

    model = 're_GEPSv3_CFSR'
    dataType = 'global_daily_1p0'
    varName = 't2m'
    minMaxs = [[-np.inf, np.inf], [-10, 13], [30, 40]]
    initTimes = [tt.format2float(d, '%Y%m%d') for d in [
        '20130117',
        # '20030112',
        # '20140119',
        # '20200101',
        # '20200125',
        # '20200117',
    ]]
    climYears = [2001, 2020]
    climType = '1day'
    # ---- 3d ---- #
    for testName, varName, minMaxs in zip(
        ['3d', '3d', '4d'],
        ['t2m', 'u10', 'u'],
        [
            [[-np.inf, np.inf],
             [-15, 15],
             [160, 180],],
            [[-np.inf, np.inf],
             [-15, 15],
             [160, 180],],
            [[-np.inf, np.inf],
             [850_00, 850_00],
             [-15, 15],
             [160, 180],],
        ]
    ):
        if test(varName, minMaxs):
            print(f'{testName} - {varName} passed!')
        else:
            print(f'{testName} - {varName} failed.')


def test_readTotalLead():
    initTimes = [
        tt.format2float(d, '%Y-%m-%d') for d in [
            '2003-01-07',
            '2015-01-12',
            '2005-07-12',
            '2017-01-12',
        ]
    ]
    dataType = 'global_daily_1p0'
    model = 're_GEPSv3_CFSR'

    varName = 't2m'
    lead = [1, 45]
    minMaxs = [lead, [-20, 20], [10, 30]]
    dataNew, dims = readTotal(
        modelName=model,
        dataType=dataType,
        varName=varName,
        minMaxs=minMaxs,
        initTimes=initTimes,
        members=[0],
    )
    print(f'{lead = }')
    print(f'{dataNew.shape[-3] = }')
    print(f'{[float(l) for l in dims[-3]]}')



def stupidReadTotal(model, dataType, varName, initTimes, minMaxs):

    def getPath(t):
        return f'{rootdir}/{model}/' \
            + f'{tt.float2format(t, '%Y/%m/%dz%H')}/E000/' \
            + f'{dataType}_{varName}.nc'
    rootdir = '/nwpr/gfs/com120/9_data/models/processed'
    data = []
    for initTime in initTimes:
        path = getPath(initTime)
        dataPart, dims = nct.ncreadByDimRange(
            fileName=path,
            varName=varName,
            minMaxs=[
                [initTime + lead for lead in minMaxs[0]],
                *minMaxs[1:],
            ],
        )
        data.append(dataPart)
        # print(dims)

    return np.array(data), dims


def stupidReadClim(model, dataType, varName, initTimes, minMaxs, climYears, climType):

    def getPath(t):
        rootdir = '/nwpr/gfs/com120/9_data/models/processed'
        return tt.float2format(
            t,
            f'{rootdir}/{model}/clim/E000/{climType}/'
            f'{varName}/{dataType}_{varName}_%m%d_'
            f'{'_'.join([str(y) for y in climYears])}_{climType}.nc'
        )

    data = []
    for iInitTime, initTime in enumerate(initTimes):
        path = getPath(initTime)
        dataPart, dims = nct.ncreadByDimRange(
            fileName=path,
            varName=varName,
            minMaxs=minMaxs,
            decodeTime=False
        )
        data.append(dataPart)

    return np.array(data, ), dims
