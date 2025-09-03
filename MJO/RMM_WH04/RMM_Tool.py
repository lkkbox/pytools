#!/nwpr/gfs/com120/.conda/envs/rd/bin/python
import xarray as xr
import numpy as np
import netCDF4 as nc
from scipy.ndimage import uniform_filter1d
import pytools.timetools as tt
import pytools.readtools.readtools as rt
import pytools.caltools as ct
from calendar import isleap

class RMM_Tool:

  def __init__(r):
    r.root_dir = '/nwpr/gfs/com120/0_tools/MJO/RMM_WH04/'
    r.read_eof_mode()
    return

  def read_eof_mode(r):
    r.fn_obs_eof  =  r.root_dir + 'obs_anom/MJO_EOF_PATTERN.nc'
    with nc.Dataset( r.fn_obs_eof, 'r') as h:
      r.eof_obs = h['EOF'][:]
      r.std_pc1 = h.getncattr('std_pc1')
      r.std_pc2 = h.getncattr('std_pc2')
      r.zavg_std_olr  = h.getncattr('zavg_std_olr')
      r.zavg_std_u850 = h.getncattr('zavg_std_u850')
      r.zavg_std_u200 = h.getncattr('zavg_std_u200')

  def read_obs_anom(r, ts, te):
    def read_clim( vn):
      fn = f'/nwpr/gfs/com120/9_data/RMM_MJO/clim/{vn}.nc'
      with xr.open_dataset( fn ) as h:
        var = h[vn2[vn]].sortby('lat')                  \
                        .interp( lon=LON, kwargs={'fill_value':'extrapolate'})      \
                        .sel( lat=slice(-15,15))        
      var = np.nanmean( var, axis=1)
      return var

    def read_olr_total( ts, te):
      print(' olr..', end='', flush=True)
      fn = '/nwpr/gfs/com120/9_data/RMM_MJO/total/olr/olr.nc'
      ts = tt.float2format( ts )
      te = tt.float2format( te )
      with xr.open_dataset( fn) as h:
        var = h['olr'].sortby('lat')                              \
                      .sel( lat=slice(-15,15), time=slice(ts,te)) \
                      .interp( lon=LON, kwargs={'fill_value':'extrapolate'})    
        time = var['time']
      var = np.nanmean( var, axis=1)
      time = tt.ymd2float( time )
      return var, time

    def read_u_total( vn, ts, te):
      print(f' {vn}..', end='', flush=True)
      fn = '/nwpr/gfs/com120/9_data/RMM_MJO/total/{vn}/ERA5_{vn}_{year:04.0f}{month:02.0f}_r720x360_1day.nc'
      timeids = [ tt.year(t)*100 + tt.month(t) for t in range( int(ts), int(te)+1)]
      timeids = sorted(list(set(timeids)))

      ts = tt.float2format( ts )
      te = tt.float2format( te )
      
      for timeid in timeids:
        year  = np.floor(timeid/100)
        month = timeid%100
        with xr.open_dataset( fn.format( vn=vn, year=year, month=month ), decode_times=False ) as h:
          varSlice = h['u'].sortby('lat')              \
                           .sel( lat=slice(-15,15))    \
                           .interp( lon=LON, kwargs={'fill_value':'extrapolate'})
          timeMin = tt.ymd2float( int(year), int(month), 1)
          timeSlice = np.array([timeMin + i for i in range(varSlice.shape[0])])

        varSlice = np.nanmean( varSlice, axis=1)
        if varSlice.ndim < 3:
          varSlice = np.tile( varSlice, (1,1))

        if timeid == list(timeids)[0]:
          var  = varSlice
          time = timeSlice
        else:
          var  = np.concatenate([var , varSlice ], axis=0)
          time = np.concatenate([time, timeSlice], axis=0)

      return var, time

    def get_anom( total, clim, time):
      iday = [ t - tt.ymd2float( tt.year(t), 1, 1) for t in time]
      iday = [ i+1 if not isleap(yr) and i > 60 else i for i, yr in zip(iday, [tt.year(t) for t in time]) ]
      iday = [ int(i) for i in iday]

      anom = total - clim[iday, :]
      return anom

    def delete_outside( vn, total, time):
      out = np.where( np.logical_or( time < min_time, max_time < time ))[0]
      if len( out ): 
        print(f' removing {len(out)} records from {vn}..', end='', flush=True)
        total = np.delete( total, out, axis=0)
        time = np.delete( time, out, axis=0)
      return total, time

    # vn2 = {'olr': 'olr', 'u850':'u', 'u200':'u'}
    # LON = np.r_[0:360:2.5]

    # print('[RMM Tool]: reading clim..', end='', flush=True)
    # olr_clim  = read_clim( 'olr')
    # u850_clim = read_clim( 'u850')
    # u200_clim = read_clim( 'u200')

    # print(' total..', end='', flush=True)
    # olr_total, olr_time   = read_olr_total( ts, te)
    # u200_total, u200_time = read_u_total( 'u200', ts, te)
    # u850_total, u850_time = read_u_total( 'u850', ts, te)

    # # TODO...

    # read anom
    olr_anom, olr_time, olr_lat, olr_lon = rt.cbo_olr_anom_day_2p5([0, 360], [-15, 15], [ts, te])
    u200_anom, u200_time, u200_lat, u200_lon = rt.era5_u200_anom_day_0p5([0, 360], [-15, 15], [ts, te])
    u850_anom, u850_time, u850_lat, u850_lon = rt.era5_u850_anom_day_0p5([0, 360], [-15, 15], [ts, te])

    # mermean
    olr_anom = np.nanmean( olr_anom, axis=1)
    u200_anom = np.nanmean( u200_anom, axis=1)
    u850_anom = np.nanmean( u850_anom, axis=1)

    # interp
    LON = np.r_[0:360:2.5]
    olr_anom = ct.interp_1d(olr_lon, olr_anom, LON, 1)
    u850_anom = ct.interp_1d(u850_lon, u850_anom, LON, 1)
    u200_anom = ct.interp_1d(u200_lon, u200_anom, LON, 1)

    # make sure they have the same time range
    min_time = np.max([ np.min(olr_time), np.min(u200_time), np.min(u850_time)])
    max_time = np.min([ np.max(olr_time), np.max(u200_time), np.max(u850_time)])
    olr_total, olr_time   = delete_outside( 'olr',  olr_anom, olr_time )
    u850_total, u850_time = delete_outside( 'u850', u850_anom, u850_time )
    u200_total, u200_time = delete_outside( 'u200', u200_anom, u200_time )

    print(f' => anomaly time = {tt.float2format(min_time)} - {tt.float2format(max_time)}')
    r.obs_olr  = olr_anom
    r.obs_u850 = u850_anom
    r.obs_u200 = u200_anom
    r.obs_time = np.array( olr_time )
    return

  def get_obs_pcs( r, ts, te):
    r.read_obs_anom( ts - 120, te)
    r.get_pcs( olr=r.obs_olr, u850=r.obs_u850, u200=r.obs_u200)
    r.pc1 = r.pc1[120:]
    r.pc2 = r.pc2[120:]
    r.pc_time = r.obs_time[120:]
    return

  def get_pcs( r, olr, u850, u200, sub120=True):
    # input shape: [ nt, nx]

    # checks
    ok, msg = True, ''
    if olr.shape != u850.shape:
      ok, msg = False, f'OLR and U850 have different shapes. {olr.shape} vs. {u850.shape}'
    if olr.shape != u200.shape:
      ok, msg = False, f'OLR and U200 have different shapes. {olr.shape} vs. {u200.shape}'
    if len(olr.shape) != 2:
      ok, msg = False, 'OLR must be a 2d array'
    if sub120 and olr.shape[0] <= 120:
      ok, msg = False, 'NT must be larger than 120'
    if olr.shape[1] != 144:
      ok, msg = False, 'NX must be 144'
    if not ok:
      print('ERROR: ' + msg)
      print('       pcs not calculated')
      return

    # normalize
    olr  = olr  / r.zavg_std_olr
    u850 = u850 / r.zavg_std_u850
    u200 = u200 / r.zavg_std_u200

    # concatenate 
    cdata = np.concatenate( (olr, u850, u200), axis=1)

    # remove pre 120d
    cdata[ np.isnan( cdata)] = 0.0
    if sub120:
      nsmooth = 121
      mavg = uniform_filter1d( cdata, nsmooth, axis=0, mode='nearest')
      ts = int( (nsmooth-1)/2 )
      cdata[nsmooth-1:,:] -= mavg[ts:-ts,:]

    # get pc1 & pc2 
    r.pc1 = np.dot( r.eof_obs[0,:], np.transpose(cdata))
    r.pc2 = np.dot( r.eof_obs[1,:], np.transpose(cdata))

    r.pc1 /= r.std_pc1 
    r.pc2 /= r.std_pc2

    return r.pc1, r.pc2

  # def phase_diagram(r):
  #   fig, ax = plt.subplots( figsize=(7,7))

  #   ##
  #   angles = np.linspace( 0, 2*np.pi, 200)
  #   ax.plot( np.cos(angles), np.sin(angles), color='k', linewidth=0.5)

  #   thisStyle = {'color':'k', 'linewidth':0.5, 'linestyle':'--'}
  #   ax.plot( [ 0,  0], [ 1, 4], **thisStyle)
  #   ax.plot( [ 0,  0], [-1,-4], **thisStyle)
  #   ax.plot( [ 1,  4], [ 0, 0], **thisStyle)
  #   ax.plot( [-1, -4], [ 0, 0], **thisStyle)
  #   s2 = np.sqrt(2)/2
  #   ax.plot( [-s2,  -4], [-s2, -4], **thisStyle)
  #   ax.plot( [ s2,   4], [-s2, -4], **thisStyle)
  #   ax.plot( [-s2,  -4], [ s2,  4], **thisStyle)
  #   ax.plot( [ s2,   4], [ s2,  4], **thisStyle)

  #   thisStyle = {'color':'k', 'fontsize':14}
  #   d1, d2 = 1.5, 3.5
  #   ax.text( -d2, -d1, str(1), **thisStyle)
  #   ax.text( -d1, -d2, str(2), **thisStyle)
  #   ax.text(  d1, -d2, str(3), **thisStyle)
  #   ax.text(  d2, -d1, str(4), **thisStyle)
  #   ax.text(  d2,  d1, str(5), **thisStyle)
  #   ax.text(  d1,  d2, str(6), **thisStyle)
  #   ax.text( -d1,  d2, str(7), **thisStyle)
  #   ax.text( -d2,  d1, str(8), **thisStyle)

  #   thisStyle = {'verticalalignment': 'center', 'horizontalalignment': 'center', 'fontsize': 14}
  #   ax.text(   0, -3.5, 'Indian\nOcean',           rotation=0,   **thisStyle)
  #   ax.text( 3.5,    0, 'Maritime\nContinent',     rotation=-90, **thisStyle)
  #   ax.text(   0, +3.5, 'Western\nPacific',        rotation=0,   **thisStyle)
  #   ax.text(-3.5,    0, 'West. Hemi.\nand Africa', rotation=90,  **thisStyle)

  #   ax.axis('equal')
  #   ax.set_xticks( np.r_[-4:4.5:1])
  #   ax.set_yticks( np.r_[-4:4.5:1])
  #   ax.set_xticks( np.r_[-4:4.5:0.5], minor=True)
  #   ax.set_yticks( np.r_[-4:4.5:0.5], minor=True)
  #   ax.set_xlim((-4.0,4.0))
  #   ax.set_ylim((-4.0,4.0))

  #   ax.set_xlabel('PC1')
  #   ax.set_ylabel('PC2')

  #   ax.tick_params( axis='both', which='major', length=8)
  #   ax.tick_params( axis='both', which='minor', length=4)
  #   return fig, ax
  
  def calPhase(r, pc1, pc2):
    angleDeg = np.angle(pc1 + 1j * pc2) / np.pi * 180
    phase = np.nan * np.ones_like(pc1)

    phase[( 0<= angleDeg) & (angleDeg < 45)] = 5
    phase[( 45<= angleDeg) & (angleDeg < 90)] = 6
    phase[( 90<= angleDeg) & (angleDeg < 135)] = 7
    phase[( 135<= angleDeg) & (angleDeg <= 180)] = 8
    phase[( -180<= angleDeg) & (angleDeg < -135)] = 1
    phase[( -135<= angleDeg) & (angleDeg < -90)] = 2
    phase[( -90<= angleDeg) & (angleDeg < -45)] = 3
    phase[( -45<= angleDeg) & (angleDeg < 0)] = 4
    return phase



if __name__ == '__main__':
  import pytools.nctools as nct
  r = RMM_Tool()
  r.get_obs_pcs( ts=tt.ymd2float( 2023, 12, 1), te=tt.ymd2float( 2024, 9, 30))
  nct.save(
    '/nwpr/gfs/com120/9_data/RMM_MJO/rmm.nc',
    {
      'pc1': r.pc1,
      'time': r.pc_time
    }
  )
  nct.save(
    '/nwpr/gfs/com120/9_data/RMM_MJO/rmm.nc',
    {
      'pc2': r.pc2,
      'time': r.pc_time
    }, overwrite=True
  )
  