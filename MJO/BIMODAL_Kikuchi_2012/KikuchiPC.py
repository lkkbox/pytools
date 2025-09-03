#!/nwpr/gfs/com120/.conda/envs/rd/bin/python
from pytools.nctools import read, save
from pytools.readtools.readtools import cbo_olr_anom_day_2p5
import pytools.timetools as tt
import numpy as np
from scipy.ndimage import uniform_filter1d


class KikuchiPC:
  def __init__(s):
    s.read_eof_modes()
  
  def read_eof_modes(s):
    print( ' reading modes..', end='', flush=True)
    s.modeFileName = '/nwpr/gfs/com120/0_tools/MJO/BIMODAL_Kikuchi_2012/modes.nc'
    s.mode_DJFMA = read( s.modeFileName, 'mode_DJFMA')
    s.mode_JJASO = read( s.modeFileName, 'mode_JJASO')
    s.std_DJFMA = np.sqrt( np.sum( s.mode_DJFMA ** 2, axis=(1,2,3) ) )
    s.std_JJASO = np.sqrt( np.sum( s.mode_JJASO ** 2, axis=(1,2,3) ) )
    print( f' -> shape={s.mode_DJFMA.shape}')

  def read_obs_anom_day_2p5(s, ts=-np.inf, te=np.inf):
    print( ' reading obs olr anomalies..', end='', flush=True)
    s.obs_olr, s.obs_time, s.obs_lat, s.obs_lon = cbo_olr_anom_day_2p5(
      minMaxX   = [  0,  360],
      minMaxY   = [-30,   30],
      minMaxT   = [ts, te],
      climYears = [2006, 2020],
      climType  = '3harm',
    )
    print(f'  -> shape = {s.obs_olr.shape}')

  def getPCstd( s):
    s.read_obs_anom_day_2p5( s, ts = tt.ymd2float( 2006, 1, 1) - 40, te = tt.ymd2float( 2020, 12, 31 ))
    s.getPCs( s, s.obs_olr)

  def getPCs( s, olr):

    # checks
    ok, msg = True, ''
    if len(olr.shape) != 3:
      ok, msg = False, msg + 'OLR must be a 3d array '
    if olr.shape[2] != 144:
      ok, msg = False, msg + ' NX must be 144 '
    if olr.shape[1] !=  25:
      ok, msg = False, msg + ' NY must be 25'
    if olr.shape[0] < 41:
      ok, msg = False, msg + ' NT mst be >= 41'
    if not ok:
      print('ERROR: ' + msg)
      print('       pcs not calculated')
      return

    nt, ny, nx = olr.shape

    # remove previous 40 days average
    olr_filtered = np.nan * np.ones( (nt-40, ny, nx) )
    olr_filtered = [ olr[i+40,:] - np.nanmean( olr[i:i+40,:] ) for i in range( nt - 40)]

    # running mean
    olr_filtered = uniform_filter1d( olr_filtered, 5, axis=0, mode='wrap')

    # reshaping the olr for EEOF projection
    nt_filtered = nt - 40
    olr_filtered3 = np.nan * np.ones( ( nt_filtered - 10, 1, 3, ny, nx) ) # t, mode, pentad y, x
    olr_filtered3[ :, 0, 0, :, : ] = olr_filtered[  0 : nt_filtered - 10, :, :]
    olr_filtered3[ :, 0, 1, :, : ] = olr_filtered[  5 : nt_filtered -  5, :, :]
    olr_filtered3[ :, 0, 2, :, : ] = olr_filtered[ 10 : nt_filtered -  0, :, :]

    s.pcs_DJFMA = np.nansum( olr_filtered3 * s.mode_DJFMA, axis=(2,3,4) )
    s.pcs_JJASO = np.nansum( olr_filtered3 * s.mode_JJASO, axis=(2,3,4) )


    print(f' shape of PCs:{s.pcs_DJFMA.shape}')
    return


if __name__ == '__main__':
  k = KikuchiPC()
  k.read_obs_anom_day_2p5( ts=tt.ymd2float( 2006, 1, 1), te=tt.ymd2float( 2006, 12, 31))
  k.getPCs( k.obs_olr )

  print(' std = ')
  print( np.std( k.pcs_DJFMA ))
  print( np.mean( k.pcs_DJFMA ))
  print( np.std( k.pcs_JJASO ))

  # save( 
  #   'OBS_PC.nc', {
  #     'PC_DJFMA': k.pcs_djfma,
  #     'time': k.obs_time[10:], 
  #     'imode': [1, 2],
  #     },
  #   overwrite = True
  #   )
  # save( 
  #   'OBS_PC.nc', {
  #     'PC_JJASO': k.pcs_jjaso,
  #     'time': k.obs_time[10:], 
  #     'imode': [1, 2],
  #     },
  #   overwrite = True
  # )