from .. import timetools as tt
from ..readtools import multiNcRead as mread
import numpy as np


def _getDefaultSourceGridFreq(varName):
    if varName == 'olr':
        return 'NOAA_OLR', None, None 
    elif varName == 'prec':
        return 'CMORPH', '0p5', 'daymean'
    elif varName in ['u', 'v', 'w', 't', 'q', 'z']:
        return 'era5_prs_daymean', None, None
    elif varName in ['u10', 'v10', 't2m', 'pw', 'mslp']:
        return 'era5_sfc_daymean', None, None
    elif varName in ['sst']:
        return 'OISST', None, None
    else:
        raise NotImplementedError(f'{varName = }, try specifying the data source or modify the paths set in this script.')

    
def _removeDuplicates(inList):
    outList = []
    for element in inList:
        if element not in outList:
            outList.append(element)
    return outList


def total(varName, minMaxs, source=None, grid=None, freq=None, root=None):
    minMaxs2 = minMaxs.copy()
    if source is None:
        source, grid, freq = _getDefaultSourceGridFreq(varName)
    if root is None:
        root = '/nwpr/gfs/com120/9_data'


    if tt.year(minMaxs2[0][0]) > 2020 and source == 'era5_prs_daymean':
        source = 'era5_prs_daymean_nrt'
    elif tt.year(minMaxs2[0][0]) >= 2025 and source == 'CMORPH':
        source = 'CMORPH_nrt'
        

    ncVarName = varName
    scale = 1.0
    if source == 'NOAA_OLR':
        dataRoot = f'{root}/NOAA_OLR'
        paths = [f'{dataRoot}/olr.cbo-1deg.day.mean.nc']
        stackedAlong = 0

    elif source == 'OISST':
        dataRoot = f'{root}/OISST/v_2p1/daymean'
        paths = [
            f'{dataRoot}/sst.day.mean.{tt.year(date)}.nc'
            for date in [
                minMaxs2[0][0] + i for i in range(int(minMaxs2[0][1] - minMaxs2[0][0] + 1))
            ]
        ]
        ncVarName = 'sst'
        stackedAlong = 0

    elif source == 'CMORPH':
        dataRoot = f'{root}/{source}'
        paths = [
            f'{dataRoot}/{freq}/{grid}/{source}_{tt.year(date)}_{grid}.nc'
            for date in [
                minMaxs2[0][0] + i for i in range(int(minMaxs2[0][1] - minMaxs2[0][0] + 1))
            ]
        ]
        stackedAlong = 0
        ncVarName = 'cmorph'

    elif source == 'CMORPH_nrt':
        dataRoot = f'{root}/CMORPH/download/v0'
        paths = [
            tt.float2format(date, f'{dataRoot}/CMORPH_V0.x_ADJ_0.25deg-DLY_00Z_%Y%m%d.nc')
            for date in [
                minMaxs2[0][0] + i for i in range(int(minMaxs2[0][1] - minMaxs2[0][0] + 1))
            ]
        ]
        stackedAlong = 0
        ncVarName = 'cmorph'

    elif source=='era5_prs_6hr':
        dataRoot = f'{root}/ERA5/q_budget/PRS'
        paths = []
        time = minMaxs[0][0]

        for i in range(9999):
            if i == 9998:
                raise RuntimeError('are you sure we should read so MANYY FILES?')

            if time > minMaxs[0][1]:
                break

            path = tt.float2format(
                time,
                f'{dataRoot}/{varName.upper()}/%Y/ERA5_PRS_{varName.upper()}_%Y%m%d-%H00.nc'
            )
            paths.append(path)

            time += 0.25

        stackedAlong = 0

    # elif source=='era5_prs_6hr':
    #     dataRoot = f'{root}/ERA5/q_budget/raw'
    #     paths = [
    #         tt.float2format(
    #             date,
    #             f'{dataRoot}/{varName}/%Y/ERA5_{varName}_%Y%m%d_tropIoPo_3hr.nc'
    #         ) for date in [
    #             minMaxs2[0][0] + i for i in range(int(minMaxs2[0][1] - minMaxs2[0][0] + 1))
    #         ]
    #     ]
    #     stackedAlong = 0

    elif source == 'era5_prs_daymean':
        dataRoot = f'{root}/ERA5/daymean/PRS'
        paths = [
            tt.float2format(
                date,
                f'{dataRoot}/{varName}/ERA5_{varName}_%Y%m_r720x360_1day.nc'
            ) for date in [
                minMaxs2[0][0] + i for i in range(int(minMaxs2[0][1] - minMaxs2[0][0] + 1))
            ]
        ]
        stackedAlong = 0
        if varName == 'z':
            scale = 1/9.80665  # m2/s2 -> m

    elif source == 'era5_sfc_daymean':
        dataRoot = f'{root}/ERA5/daymean/SFC'
        if varName == 'tcwv' or varName == 'pw':
            pathFormat = f'{dataRoot}/ERA5_tcwv_%Y_day.nc'
            ncVarName = 'tcwv'
        else:
            pathFormat = f'{dataRoot}/ERA5_sfc_%Y_day.nc'
            if varName == 'mslp':
                ncVarName = 'msl'

        paths = [
            tt.float2format(date, pathFormat) 
            for date in [
                minMaxs2[0][0] + i for i in range(int(minMaxs2[0][1] - minMaxs2[0][0] + 1))
            ]
        ]
        stackedAlong = 0

    elif source in ['era5_prs_daymean_nrt', 'era5_daymean_nrt', 'era5_sfc_daymean_nrt']:
        if varName == 'mslp':
            ncVarName = 'msl'
        if varName == 'pw':
            varName = 'tcwv'
            ncVarName = 'tcwv'
        dataRoot = f'{root}/ERA5/nearRealTime/daymean'
        paths = [
            tt.float2format(
                date,
                f'{dataRoot}/ERA5_{varName}_%Y%m%d_r720x360_1day.nc'
            ) for date in [
                minMaxs2[0][0] + i for i in range(int(minMaxs2[0][1] - minMaxs2[0][0] + 1))
            ]
        ]
        if varName == 'z':
            scale = 1/9.80665  # m2/s2 -> m
        stackedAlong = 0
        minMaxs2[0][1] += 0.99
    else:
        raise NotImplementedError(f'{source = }')

    paths = _removeDuplicates(paths)
    data, dims = mread.read(paths, ncVarName, minMaxs2, stackedAlong=stackedAlong)
    data = data * scale
    return data, dims


def clim(varName, minMaxs, source=None, grid=None, freq=None, 
         climYears=[2001, 2020], climType='5dma', root=None):
    if source is None:
        source, grid, freq = _getDefaultSourceGridFreq(varName)

    if root is None:
        root = '/nwpr/gfs/com120/9_data'


    year0, iDimT = 2000, 0 # default values
    stackedAlong = 0
    ncVarName = varName
    scale = 1.0
    minMaxs2 = minMaxs.copy()
    if minMaxs2[0][1] % 1 == 0:
        minMaxs2[0][1] += 0.99

    if varName == 'olr':
        paths = [
            f'{root}/NOAA_OLR/olr_clim_{climYears[0]}_{climYears[1]}_1p0_{climType}.nc'
        ]
    elif source in [
        'era5_prs_daymean',
        'era5_sfc_daymean',
        'era5_prs_daymean_nrt',
        'era5_daymean_nrt',
        'era5_sfc_daymean_nrt'
    ]:
        dataRoot = f'{root}/ERA5/clim_5dma'
        if varName in ['u', 'v', 'w', 't', 'q', 'z', 't2m']:
            fileVarName = varName
        elif varName in ['u10', 'v10', 't2m', 'mslp']:
            fileVarName = 'sfc'
        elif varName == 'pw':
            fileVarName = 'tcwv'
            ncVarName = 'tcwv'
        else:
            raise NotImplementedError(f'{varName = }')

        if fileVarName not in ['sfc', 'tcwv']:
            paths = [f'{dataRoot}/ERA5_{fileVarName}_clim_{climYears[0]}_{climYears[1]}_r720x360_{climType}.nc']
        else:
            paths = [f'{dataRoot}/ERA5_{fileVarName}_clim_{climYears[0]}_{climYears[1]}_{climType}.nc']
        if varName == 'mslp':
            ncVarName = 'msl'


    elif source == 'CMORPH' or source == 'CMORPH_nrt':
        dataRoot = f'{root}/CMORPH/clim'
        paths = [f'{dataRoot}/CMORPH_clim_{climYears[0]}_{climYears[1]}_0p5_{climType}.nc']
        ncVarName = 'cmorph'
    else:
        raise NotImplementedError(f'{varName =}, {source = }')

    # find the time to read
    t1, t2 = minMaxs2[iDimT]
    j1, j2 = tt.dayOfYear229(t1), tt.dayOfYear229(t2)
    y1, y2 = tt.year(t1), tt.year(t2)
    c1 = tt.ymd2float(year0, 1, 1) + j1 - 1
    c2 = tt.ymd2float(year0, 1, 1) + j2 - 1

    if y1 == y2:
        minMaxs2[iDimT] = [c1, c2]
        data, dims = mread.read(paths, ncVarName, minMaxs2, stackedAlong=stackedAlong)
    elif j2 >= j1 - 1: # for a full year
        minMaxs2[iDimT] = [None, None]
        data, dims = mread.read(paths, ncVarName, minMaxs2, stackedAlong=stackedAlong)
    else: # an incomplete year, separate dates
        minMaxs2[iDimT] = [None, c2]
        data1, dims1 = mread.read(paths, ncVarName, minMaxs2, stackedAlong=stackedAlong)
        minMaxs2[iDimT] = [c1, None]
        data2, dims2 = mread.read(paths, ncVarName, minMaxs2, stackedAlong=stackedAlong)
        data = np.concatenate((data1, data2), axis=stackedAlong)
        dims = dims1
        dims[stackedAlong] = np.concatenate((dims1[stackedAlong], dims2[stackedAlong]))
        

    data = data * scale
    return data, dims


def anomaly(varName, minMaxs, source=None, grid=None, freq=None,
            climYears=[2001, 2020], climType='5dma', interpolate_to=None,
            root=None
            ):
    if source is None:
        source, grid, freq = _getDefaultSourceGridFreq(varName)

    dataTotal, dimsTotal = total(varName, minMaxs, source, grid, freq, root)
    dataClim, dimsClim = clim(varName, minMaxs, source, grid, freq, climYears, climType, root)
    if interpolate_to is not None:
        from ..caltools import interp_1d
        if interpolate_to.lower() == 'total':
            dataClim = interp_1d(dimsClim[-1], dataClim, dimsTotal[-1], -1, True)
            dataClim = interp_1d(dimsClim[-2], dataClim, dimsTotal[-2], -2, True)
        elif interpolate_to.lower() == 'clim':
            dataTotal = interp_1d(dimsTotal[-1], dataTotal, dimsClim[-1], -1, True)
            dataTotal = interp_1d(dimsTotal[-2], dataTotal, dimsClim[-2], -2, True)
        else:
            raise NotImplementedError(f'{interpolate_to = }')
    elif dataTotal.shape[-2:] != dataClim.shape[-2:]:
        raise ValueError('Dimension are mismatched between clim and total.'
                         'Set interpolate_to to "clim" or "total" for interpolation.')


    jdTotal = [tt.dayOfYear229(int(d)) for d in dimsTotal[0]]
    jdClim = [tt.dayOfYear229(int(d)) for d in dimsClim[0]]
    iDayClims = [jdClim.index(d) for d in jdTotal]
    data = dataTotal - dataClim[iDayClims, :]
    return data, dimsTotal




def test():
    tste = [tt.ymd2float(2023, 1, 5), tt.ymd2float(2024, 1, 3),]
    print(f' total test')
    olr, dims = total(
        varName='olr',
        minMaxs=[tste, [-5, 5], [120, 150]],
    )
    print(f'{np.mean(olr) = }')
    print(f'{olr.shape = }')

    print(f' clim test')
    olr, dims = anomaly(
        varName='olr',
        minMaxs=[tste, [-5, 5], [120, 150]],
    )
    print([len(d) for d in dims])
    print([tt.float2format(d) for d in dims[0]])
    print(f'{np.mean(olr) = }')
    print(f'{olr.shape = }')
