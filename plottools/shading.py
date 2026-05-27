from matplotlib.axes import Axes
from typing import Literal
import numpy as np
from .colormaps import get_cmap_colors


def contourf(ax: Axes, x, y, z, levels, cmap="viridis", *arg, **kwarg):
    """return the contourf handle"""
    z2, levels2 = _rescale(z, levels)
    colors = get_cmap_colors(cmap, len(levels2) + 1)
    hcf = ax.contourf(
        x, y, z2, *arg, levels=levels2, colors=colors, extend="both", **kwarg
    )
    return hcf


def _rescale(z, levels) -> tuple[np.ndarray, list[int]]:
    z = np.array(z)
    z2 = np.nan * np.ones_like(z)

    levels2 = [i for i in range(len(levels))]

    mask = z <= levels[0]
    deltaLevel = levels[1] - levels[0]
    z2[mask] = (z[mask] - levels[0]) / deltaLevel

    for iz0, (level0, level1) in enumerate(zip(levels, levels[1:])):
        mask = (level0 <= z) & (z < level1)
        z2[mask] = (z[mask] - level0) / (level1 - level0) + iz0

    mask = levels[-1] <= z
    deltaLevel = levels[-1] - levels[-2]
    z2[mask] = (z[mask] - levels[-1]) / deltaLevel + levels2[-1]
    return z2, levels2


def colorbar(
    ax: Axes,
    levels,
    cmap: str,
    orientation: Literal["h", "v"] = "h",
):
    ncolors = len(levels) + 1
    x = list(range(ncolors))
    y = [1, 2]
    z = [
        [
            levels[0] - 0.5 * (levels[1] - levels[0]),
            *[0.5 * (l0 + l1) for l0, l1 in zip(levels[:-1], levels[1:])],
            levels[-1] + 0.5 * (levels[-1] - levels[-2]),
        ]
    ] * 2
    ticks = [0.5 + i for i in range(len(levels))]
    tickLabels = [str(lv) for lv in levels]

    if orientation == "v":  # swap x, y
        x, y = y, x
        z = list(zip(*z))

    contourf(
        ax,
        x,
        y,
        z,
        levels,
        cmap,
    )

    ax.set_xlim(x[0], x[-1])
    ax.set_ylim(y[0], y[-1])

    if orientation == "v":
        # xOrY = "y"
        ax.set_xticks([])
        ax.set_yticks(ticks)
        ax.set_yticklabels(tickLabels)
    else:
        # xOrY = "x"
        ax.set_yticks([])
        ax.set_xticks(ticks)
        ax.set_xticklabels(tickLabels)
