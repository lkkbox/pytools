#!/nwpr/gfs/com120/.conda/envs/rd/bin/python 
from pytools.readtools.readtools import cbo_olr_total_day_2p5
from pytools.caltools import bandPassFilter
import pytools.timetools as tt
import pytools.nctools as nct
import numpy as np
from eofs.standard import Eof
# from scipy.interpolate import griddata


def eeof( months ):
  nt, ny, nx = olr.shape
  N_EOF = 2

  var = olr.copy()
  # select months
  for v, t in zip( var, time ):
    if tt.month( t ) not in months:
      v[:] = np.nan 
    
  # concatenate -10, -5, 0 days
  var3 = np.nan * np.ones( (nt - 10, ny, nx * 3) )
  var3[ :, :, 0*nx : 1*nx ] = var[  0:(nt-10) , :, :]
  var3[ :, :, 1*nx : 2*nx ] = var[  5:(nt- 5) , :, :]
  var3[ :, :, 2*nx : 3*nx ] = var[ 10:(nt- 0) , :, :]

  # remove days of nans
  any_nan_mask = np.isnan( var3 ).any(axis=(1, 2))  # Check for NaN across x and y
  var3 = var3[~any_nan_mask]

  # eof
  sqrtcoslat = np.sqrt( np.cos( lat/180 * np.pi ) ) # weighting
  var3 *= sqrtcoslat[ :, None ]
  solver  = Eof( var3 )
  eigvec3 = solver.eofs( eofscaling=2, neofs=N_EOF)
  expvar  = solver.varianceFraction( neigs=N_EOF)

  # reshape
  eigvec = np.nan * np.ones( (2, 3, ny, nx))
  for imode in range( N_EOF ):
    eigvec[ imode, 0, :] = eigvec3[ imode, :, 0*nx : 1*nx]
    eigvec[ imode, 1, :] = eigvec3[ imode, :, 1*nx : 2*nx]
    eigvec[ imode, 2, :] = eigvec3[ imode, :, 2*nx : 3*nx]
  return eigvec, expvar

if __name__ == '__main__':

  # boundaries
  minMaxX = [  0, 360]
  minMaxY = [-30,  30]
  minMaxT = [tt.ymd2float( 1991, 1, 1), tt.ymd2float( 2020, 12, 31)]
  fn_out = './modes.nc'

  # read data
  print( f'reading..', end='', flush=True)
  olr, time, lat, lon = cbo_olr_total_day_2p5( 
    minMaxX=minMaxX, 
    minMaxY=minMaxY, 
    minMaxT=minMaxT,
    )
  print(f' olr.shape = {olr.shape}', end='', flush=True)

  # band pass filtering between 25 - 90 days
  olr = bandPassFilter( olr, [25, 90], axis=0)
  
  # select months
  mode_winter, expvar_winter = eeof([12, 1, 2, 3,  4] )
  mode_summer, expvar_summer = eeof([ 6, 7, 8, 9, 10] )

  # adjust sign and order
  if minMaxT == [tt.ymd2float( 1991, 1, 1), tt.ymd2float( 2020, 12, 31)]:
    mode_winter[ 1, :] *= -1 
    mode_summer = mode_summer[ ::-1, :]
    mode_summer[ 1, :] *= -1
    expvar_summer = expvar_summer[::-1]

  # save 
  print(f' writing to {fn_out}', end='', flush=True)
  nct.save( 
    fn_out,
    {
      'mode_DJFMA' : mode_winter, 
      'imode': [1, 2],
      'ipentad': [-2, -1, 0],
      'lat': lat,
      'lon': lon,
    }, 
    overwrite=True
    )
  
  nct.save( 
    fn_out,
    {
      'expvar_DJFMA' : expvar_winter, 
      'imode': [1, 2],
    }, 
    overwrite=True
    )

  nct.save( 
    fn_out,
    {
      'mode_JJASO' : mode_summer, 
      'imode': [1, 2],
      'ipentad': [-2, -1, 0],
      'lat': lat,
      'lon': lon,
    }, 
    overwrite=True
    )
  
  nct.save( 
    fn_out,
    {
      'expvar_JJASO' : expvar_summer, 
      'imode': [1, 2],
    }, 
    overwrite=True
    )