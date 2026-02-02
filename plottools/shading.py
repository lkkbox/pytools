from matplotlib.axes import Axes
import numpy as np


def contourf2(
    ax: Axes,
    x,
    y,
    z,
    levels=None,
    cmap="viridis",
    plotColorbar=True,
    contourfOptions={},
    cbarOptions={},
):
    z = np.array(z)
    z2 = np.nan * np.ones_like(z)

    if levels is None:
        from ..caltools import nearest_nice_number

        levels = nearest_nice_number(
            np.percentile(z[(~np.isnan(z))], np.r_[0:110:10])
        )

    levels2 = [i for i in range(len(levels))]

    mask = z <= levels[0]
    deltaLevel = levels[1] - levels[0]
    z2[mask] = (z[mask] - levels[0]) / deltaLevel

    for iz0, (level0, level1) in enumerate(zip(levels, levels[1:])):
        mask = (level0 <= z) & (z < level1)
        z2[mask] = (z[mask] - level0) / (level1 - level0) + iz0

    mask = levels[-1] < z
    deltaLevel = levels[-1] - levels[-2]
    z2[mask] = (z[mask] - levels[-1]) / deltaLevel + levels2[-1]

    hcf = ax.contourf(
        x, y, z2, levels=levels2, cmap=cmap, extend="both", **contourfOptions
    )

    if plotColorbar:
        fig = ax.get_figure()
        cbar = fig.colorbar(hcf, ax=ax, **cbarOptions)
        cbar.set_ticks(levels2)
        cbar.set_ticklabels(levels)
    else:
        cbar = None

    return hcf, cbar


def pcolor(
    ax: Axes,
    x,
    y,
    z,
    levels=None,
    cmap="viridis",
    plotColorbar=True,
    contourfOptions={},
    cbarOptions={},
    pcolorOptions={},
):
    z = np.array(z)
    z2 = np.nan * np.ones_like(z)

    if levels is None:
        from ..caltools import nearest_nice_number

        levels = nearest_nice_number(
            np.percentile(z[(~np.isnan(z))], np.r_[0:110:10])
        )

    z[(z >= levels[-1])] = levels[-1] - 0.01 * (levels[-1] - levels[-2])
    z[(z < levels[0])] = levels[0]

    levels2 = [i for i in range(len(levels))]

    mask = z <= levels[0]
    deltaLevel = levels[1] - levels[0]
    z2[mask] = (z[mask] - levels[0]) / deltaLevel

    for iz0, (level0, level1) in enumerate(zip(levels, levels[1:])):
        mask = (level0 <= z) & (z < level1)
        z2[mask] = (z[mask] - level0) / (level1 - level0) + iz0

    mask = levels[-1] < z
    deltaLevel = levels[-1] - levels[-2]
    z2[mask] = (z[mask] - levels[-1]) / deltaLevel + levels2[-1]

    hcf = ax.pcolor(
        x,
        y,
        z2,
        vmin=levels2[0],
        vmax=levels2[-1],
        shading="nearest",
        cmap=cmap,
        **contourfOptions,
    )

    if plotColorbar:
        fig = ax.get_figure()
        cbar = fig.colorbar(hcf, ax=ax, **cbarOptions)
        cbar.set_ticks(levels2)
        cbar.set_ticklabels(levels)
    else:
        cbar = None

    return hcf, cbar
