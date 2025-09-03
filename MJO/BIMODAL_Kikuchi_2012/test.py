#!/nwpr/gfs/com120/.conda/envs/rd/bin/python
import pytools.nctools as nct
import pytools.timetools as tt
import pytools.readtools.readtools as rt

if __name__ == '__main__':
  olr, time, lat, lon = rt.cbo_olr_anom_day_2p5(
    minMaxX = [0, 360],
    minMaxY = [-40, 40],
    minMaxT = [tt.ymd2float( 2001, 1, 1), tt.ymd2float( 2001, 1, 31)],
    climYears = [2006, 2020],
    climType = '3harm',
  )
  nct.save( 
    '/nwpr/gfs/com120/messy/a.nc',
    {
      'olr': olr,
      'time': time,
      'lat': lat,
      'lon': lon,
    },
    overwrite = True,
    )