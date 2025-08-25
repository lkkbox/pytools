import matplotlib.pyplot as plt
import netCDF4 as nc
import numpy as np


def make_coastlines(infile, outfile):
    # infile='ETOPO_0p1deg.nc'
    # outfile='ETOPO_0p1deg_coastlines.nc'

    with nc.Dataset(infile, 'r') as h_ds:
        lon  = h_ds['lon'][:]
        lat  = h_ds['lat'][:]
        topo = h_ds['z'][:]

    plt.close()
    fig1,ax1=plt.subplots()
    h_coast = ax1.contour( 
        lon, lat, topo,
        levels = (0,),
        colors = 'k',
        linewidths = 1,
        linestyles = '-',
    )

    ax1.set_xlim((0,360))
    ax1.set_ylim((-90,90))


    segs = h_coast.allsegs[0]

    x = []
    y = []
    for points in segs:
        for point in points:
            x.append( point[0])
            y.append( point[1])
    x.append( np.nan)
    y.append( np.nan)

    fig2, ax2=plt.subplots()
    ax2.plot( x, y, color = 'b', linewidth = 1,)
    ax2.set_xlim((0,360))
    ax2.set_ylim((-90,90))

    npoint = len(x)
    with nc.Dataset( outfile, 'w') as h_ds:
        h_ds.createDimension( 'point', npoint)
        v_point = h_ds.createVariable( 'point', datatype='int64',  dimensions=('point',))
        v_lon   = h_ds.createVariable( 'lon',   datatype='double', dimensions=('point',))
        v_lat   = h_ds.createVariable( 'lat',   datatype='double', dimensions=('point',))
        v_point[:] = np.array( list(range(0,npoint)))
        v_lon[:]   = np.array( x)
        v_lat[:]   = np.array( y)
