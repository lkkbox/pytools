#!/nwpr/gfs/com120/.conda/envs/rd/bin/python 
import matplotlib.pyplot as plt 
import numpy as np
from pytools.nctools import read
from pytools.plottools import plotcoast, wmapaxisx, wmapaxisy


def plot1map( ax, data ):
  levels = np.r_[-15:0:3, 3:18:3]
  hcf = ax.contourf( lon, lat, data, cmap='bwr', levels=levels, extend='both')
  ax.contour( lon, lat, data, colors='k', levels=levels, linewidths=0.5, linestyles='-')
  plotcoast( ax )
  return hcf


def plot2x3( data, expvar, seasonName ):
  fig, axs = plt.subplots( nrows=3, ncols=2, layout='constrained')
  for irow in range( 3 ):
    for icol in range( 2 ):
      ax = axs[irow, icol]
      ipentad, imode = irow, icol 
      ev = expvar[imode]
      if irow == 0: ax.set_title(f'{seasonName} EEOF{imode+1} ({ev*100:.1f}%)', fontweight='bold')
      d = data[ imode, ipentad, :, :]
      hcf = plot1map( ax, d )
      if icol == 0: ax.set_ylabel(f'Pentad {ipentad-2}', fontweight='bold')
      wmapaxisy( ax, 20 )
      wmapaxisx( ax, 60 )
  fig.colorbar( hcf, orientation='horizontal' )
  fig.savefig( 'mode_'+seasonName+'.png', dpi=150)
  return fig

if __name__ == '__main__':
  filename = './modes.nc'
  eof_winter = read( filename, 'mode_DJFMA')
  eof_summer = read( filename, 'mode_JJASO')
  lon = read( filename, 'lon')
  lat = read( filename, 'lat')
  expvar_winter = read( filename, 'expvar_DJFMA')
  expvar_summer = read( filename, 'expvar_JJASO')

  fig1 = plot2x3( eof_winter, expvar_winter, 'DJFMA' )
  fig2 = plot2x3( eof_summer, expvar_summer, 'JJASO' )
  plt.show()
