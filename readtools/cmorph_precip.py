from .. import timetools as tt
from . import readtools as rt
import numpy as np

def cmorph_prec_total_day_0p5(minMaxX, minMaxY, minMaxT):
    nyears = tt.year(minMaxT[1]) - tt.year(minMaxT[0]) + 1
    for iyear in range(nyears):
        year = tt.year(minMaxT[0]) + iyear
        varSlice, timeSlice, lat, lon = rt.readw2g(**{
            'filename': f'/nwpr/gfs/com120/9_data/CMORPH/daymean/0p5/CMORPH_{year}_0p5.nc',
            'varName': 'cmorph',
            'minMaxs': [minMaxT, minMaxY, minMaxX],
            'iDimT': 0,
            'minTime': tt.ymd2float(year, 1, 1),
            'intervalTime': [1, 'day'],
        })

        if iyear == 0:
            var = varSlice
            time = timeSlice
        else:
            var = np.concatenate((var, varSlice), axis=0)
            time = np.concatenate((time, timeSlice), axis=0)

    var[(np.abs(var) > 1e3)] = np.nan
    return var, [time, lat, lon]


def cmorph_prec_clim_day_0p5(minMaxX, minMaxY, minMaxT=[-np.inf, np.inf], climYears=[2006, 2020], climType='3harm'):
    minMaxT2000 = [tt.ymd2float(2000, tt.month(t), tt.day(t)) for t in minMaxT]
    var, time, lat, lon = rt.readw2g(**{
        'filename': f'/nwpr/gfs/com120/9_data/CMORPH/clim/CMORPH_clim_{climYears[0]}_{climYears[1]}_0p5_{climType}.nc',
        'varName': 'cmorph',
        'minMaxs': [minMaxT2000, minMaxY, minMaxX],
        'iDimT': 0,
        'minTime': tt.ymd2float(2000, 1, 1),
        'intervalTime': [1, 'day'],
    })
    var[(np.abs(var) > 1e3)] = np.nan
    return var, [time, lat, lon]


def cmorph_prec_anom_day_0p5(minMaxX, minMaxY, minMaxT, climYears=[2006, 2020], climType='3harm'):
    var, dims = rt.read_anom(
        cmorph_prec_total_day_0p5,
        cmorph_prec_clim_day_0p5,
        minMaxX,
        minMaxY,
        minMaxT,
        climYears,
        climType
    )
    return var, dims

