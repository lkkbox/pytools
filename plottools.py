import netCDF4 as nc
import numpy as np


def plotbox(ax, lonwe, latsn, *args, **kwargs):
    lon = [lonwe[i] for i in [0, 1, 1, 0, 0]]
    lat = [latsn[i] for i in [1, 1, 0, 0, 1]]
    return ax.plot(lon, lat, *args, **kwargs)


def contourf2(ax, x, y, z, levels, cmap='viridis', extend='both', plotColorbar=True, cbarOptions={}):
    z = np.array(z)
    z2 = np.nan * np.ones_like(z)

    levels2 = [i for i in range(len(levels))]

    mask = (z <= levels[0])
    deltaLevel = levels[1] - levels[0]
    z2[mask] = (z[mask] - levels[0])/deltaLevel

    for iz0, (level0, level1) in enumerate(zip(levels, levels[1:])):
        mask = ((level0<=z) & (z<level1))
        z2[mask] = (z[mask] - level0)/(level1 - level0) + iz0

    mask = (levels[-1] < z)
    deltaLevel = levels[-1] - levels[-2]
    z2[mask] = (z[mask] - levels[-1])/deltaLevel + levels2[-1]

    hcf = ax.contourf(x, y, z2, levels=levels2, cmap=cmap, extend=extend)
    if plotColorbar:
        cbar = ax.get_figure().colorbar(hcf, ax=ax, **cbarOptions)
        cbar.set_ticks(levels2)
        cbar.set_ticklabels(levels)
    else:
        cbar = None
    return hcf, cbar

def contourfill(
        ax, x, y, z, levels=None, cmap='viridis',
        plotColorbar=True, contourfOptions={}, cbarOptions={},
):

    z = np.array(z)
    z2 = np.nan * np.ones_like(z)

    if levels is None:
        from caltools import nearest_nice_number
        levels = nearest_nice_number(np.percentile(z[(~np.isnan(z))], np.r_[0:110:10]))

    levels2 = [i for i in range(len(levels))]

    mask = (z <= levels[0])
    deltaLevel = levels[1] - levels[0]
    z2[mask] = (z[mask] - levels[0])/deltaLevel

    for iz0, (level0, level1) in enumerate(zip(levels, levels[1:])):
        mask = ((level0<=z) & (z<level1))
        z2[mask] = (z[mask] - level0)/(level1 - level0) + iz0

    mask = (levels[-1] < z)
    deltaLevel = levels[-1] - levels[-2]
    z2[mask] = (z[mask] - levels[-1])/deltaLevel + levels2[-1]

    hcf = ax.contourf(x, y, z2, levels=levels2, cmap=cmap, **contourfOptions)

    if plotColorbar:
        cbar = ax.get_figure().colorbar(hcf, ax=ax, **cbarOptions)
        cbar.set_ticks(levels2)
        cbar.set_ticklabels(levels)
    else:
        cbar = None

    return hcf, cbar


def strLongitudes(yticks):
    return [strLongitude(ytick) for ytick in yticks]

def strLatitudes(yticks):
    return [strLatitude(ytick) for ytick in yticks]

def strLongitude(lon):
    ntries = 0
    while lon >= 360:
        lon -= 360
        ntries += 1
        if ntries > 10:
            raise RuntimeError('unable to convert lon to string')

    while lon <= 0:
        lon += 360
        ntries += 1
        if ntries > 10:
            raise RuntimeError('unable to convert lon to string')

    if lon == 0 or lon == 180:
        x, we = lon, chr(176)
    if lon < 180:
        x, we = lon, f'{chr(176)}E'
    if lon > 180:
        x, we = 360-lon, f'{chr(176)}W'

    return str(x)+we


def strLatitude(lat):
    if lat == 0:
        y, we = lat, f'{chr(176)}'
    if lat < 0:
        y, we = -lat, f'{chr(176)}S'
    if lat > 0:
        y, we = lat, f'{chr(176)}N'
    return str(y)+we
    

def wmapaxisx(ax, xint=30):
    xlim = ax.get_xlim()
    xticks = list(range(0, 360+xint, xint))
    xticklabels = strLongitudes(xticks)
    ax.set_xticks(xticks)
    ax.set_xticklabels(xticklabels)
    ax.set_xlim(xlim)
    return


def wmapaxisy(ax, yint=10):
    ylim = ax.get_ylim()
    yticks = [
        *list(range(0, -90-yint, -yint)),
        *list(range(yint, 90+yint, yint)),
    ]
    yticklabels = strLatitudes(yticks)
    ax.set_yticks(yticks)
    ax.set_yticklabels(yticklabels)
    ax.set_ylim(ylim)
    return


def colorbarTrimDecimalZeros(cbar, levels=None):
    if levels is None:
        ticks = cbar.get_ticks()
    else:
        ticks = levels

    tickLabels = [str(t) for t in ticks]
    cbar.set_ticks(ticks)
    cbar.set_ticklabels([trimDecimalZeros(t) for t in tickLabels])


def trimDecimalZeros(str):
    if '.' not in str:
        return str
    for iDecimal, digit in enumerate(str[::-1]):
        if digit != '0':
            break
    if str[-(iDecimal+1)] == '.':
        return str[:-(iDecimal+1)]
    elif iDecimal == 0:
        return str
    else:
        return str[:-iDecimal]


def plotcoast(ax, color='grey', linewidth=0.5, linestyle='-', resolution='0p5'):
    from config import load_config
    import os

    HOME = os.environ.get('HOME')
    subPath = load_config(f'etopo_coastlines_{resolution}')
    filename = f'{HOME}/{subPath}'

    if not os.path.exists(filename):
        raise FileNotFoundError(f'coastline file={filename}')

    with nc.Dataset(filename, 'r') as h_ds:
        xlist = h_ds['lon'][:]
        ylist = h_ds['lat'][:]

    ps_xlim = ax.get_xlim()
    ps_ylim = ax.get_ylim()

    x, y = zip(
        *[
            (x, y) if (    x >= ps_xlim[0] and x <= ps_xlim[1]
                and y >= ps_ylim[0] and y <= ps_ylim[1]
                ) else (float('nan'), float('nan'))
                for x, y in zip(xlist, ylist) 
        ]
    )

    x, y = list(x), list(y)

    h_coast = ax.plot(x, y,
                      color=color,
                      linewidth=linewidth,
                      linestyle=linestyle,
                      )
    ax.set_xlim(ps_xlim)
    ax.set_ylim(ps_ylim)
    return h_coast


def titleCorner(ax, title, r_dy=0.01, cornerIndex=[0, 1], **kwargs):
    x = cornerIndex[0]
    y = cornerIndex[1] + r_dy
    ax.text(x, y, title, transform=ax.transAxes, **kwargs)  

def phase_diagram():
    fig, ax = plt.subplots(figsize=(7, 7)) # type: ignore

    ##
    angles = np.linspace(0, 2*np.pi, 200) # type: ignore
    ax.plot(np.cos(angles), np.sin(angles), color='k', linewidth=0.5) # type: ignore

    thisStyle = {'color': 'k', 'linewidth': 0.5, 'linestyle': '--'}
    ax.plot([0,  0], [1, 4], **thisStyle)
    ax.plot([0,  0], [-1, -4], **thisStyle)
    ax.plot([1,  4], [0, 0], **thisStyle)
    ax.plot([-1, -4], [0, 0], **thisStyle)
    s2 = np.sqrt(2)/2 # type: ignore
    ax.plot([-s2,  -4], [-s2, -4], **thisStyle)
    ax.plot([s2,   4], [-s2, -4], **thisStyle)
    ax.plot([-s2,  -4], [s2,  4], **thisStyle)
    ax.plot([s2,   4], [s2,  4], **thisStyle)

    thisStyle = {'color': 'k', 'fontsize': 14}
    d1, d2 = 1.5, 3.5
    ax.text(-d2, -d1, str(1), **thisStyle)
    ax.text(-d1, -d2, str(2), **thisStyle)
    ax.text(d1, -d2, str(3), **thisStyle)
    ax.text(d2, -d1, str(4), **thisStyle)
    ax.text(d2,  d1, str(5), **thisStyle)
    ax.text(d1,  d2, str(6), **thisStyle)
    ax.text(-d1,  d2, str(7), **thisStyle)
    ax.text(-d2,  d1, str(8), **thisStyle)

    thisStyle = {'verticalalignment': 'center',
                 'horizontalalignment': 'center', 'fontsize': 14}
    ax.text(0, -3.5, 'Indian\nOcean',           rotation=0,   **thisStyle)
    ax.text(3.5,    0, 'Maritime\nContinent',     rotation=-90, **thisStyle)
    ax.text(0, +3.5, 'Western\nPacific',        rotation=0,   **thisStyle)
    ax.text(-3.5,    0, 'West. Hemi.\nand Africa', rotation=90,  **thisStyle)

    ax.axis('equal')
    ax.set_xticks(np.r_[-4:4.5:1]) # type: ignore
    ax.set_yticks(np.r_[-4:4.5:1]) # type: ignore
    ax.set_xticks(np.r_[-4:4.5:0.5], minor=True) # type: ignore
    ax.set_yticks(np.r_[-4:4.5:0.5], minor=True) # type: ignore
    ax.set_xlim((-4.0, 4.0))
    ax.set_ylim((-4.0, 4.0))

    ax.set_xlabel('PC1')
    ax.set_ylabel('PC2')

    ax.tick_params(axis='both', which='major', length=8)
    ax.tick_params(axis='both', which='minor', length=4)
    return fig, ax


class FlushPrinter:
    def __init__(self):
        self.content = ''
        return

    def flushPrint(self, new_string=''):
        new_string = str(new_string)
        numErase = len(self.content)
        eraser = '\b'*numErase + ' '*numErase + '\b'*numErase
        print(eraser + new_string, flush=True, end='')
        self.content = new_string
        return

    def print(self, new_string='', **kwArgs):
        self.flushPrint('')
        print(new_string, flush=True, **kwArgs)

    def append(self, new_string):
        self.content += str(new_string)
        print(new_string, end='', flush=True)
        return

    def __del__(self):
        self.flushPrint('')
