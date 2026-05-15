from matplotlib.lines import Line2D
from matplotlib.text import Text
from typing import Literal
from matplotlib.axes import Axes
import numpy as np
from dataclasses import dataclass, field
from typing import Iterable
from copy import copy


@dataclass
class VectorConfig:
    scale: float | None = None
    headAngle: float = 40  # degree
    pivot: Literal["tail", "center", "middle", "head"] = "tail"
    rHeadLen: float = 0.3  # normalized 0-1: 1 is as long as the vector body
    headLenMax: float | None = None
    skip: int = 1
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    _aspect: float = field(init=False)  # ax ylim / xlim


def vector(
    ax: Axes,
    x: Iterable | float,
    y: Iterable | float,
    u: Iterable | float,
    v: Iterable | float,
    config: VectorConfig = VectorConfig(),
) -> tuple[list[Line2D], VectorConfig]:
    lineData = _get_line_data(ax, x, y, u, v, config)
    del x, y, u, v

    hLine = ax.plot(
        lineData[0].ravel(),
        lineData[1].ravel(),
        *config.args,
        **config.kwargs,
    )

    return hLine, config


def vector_reference(
    config: VectorConfig,
    parentAx: Axes,
    anchor: Literal["tr", "tl", "br", "bl"],
    quadrant: Literal[1, 2, 3, 4],
    rdx: float,
    rdy: float,
    magnitude: float,
    text: str = "",
    padStart: float = 0.0,  # padding units = axes width
    padText: float = 0.03,
    anchorShift: tuple[float, float] = (0, 0),
    showAxBnd: bool = False,  # for debugging
) -> tuple[list[Line2D], Text, Axes]:
    # -- create the canvas to draw the reference vector
    ax = _create_ax(parentAx, anchor, quadrant, rdx, rdy, anchorShift)

    # -- set the axis limits
    parentXlim = parentAx.get_xlim()
    parentYlim = parentAx.get_ylim()
    dx = (parentXlim[1] - parentXlim[0]) * rdx
    dy = (parentYlim[1] - parentYlim[0]) * rdy
    ax.set_xlim(0, dx)
    ax.set_ylim(0, dy)

    # -- draw the vector
    config = copy(config)
    config.pivot = "tail"  # you must force the start point
    x = padStart * dx
    y = dy / 2
    u = magnitude
    v = 0
    lineData = _get_line_data(ax, x, y, u, v, config)
    hLine = ax.plot(
        lineData[0].ravel(),
        lineData[1].ravel(),
        *config.args,
        **config.kwargs,
    )

    # -- start of text = max(line_x) + padText
    xText = np.nanmax(lineData[0]) + padText * dx
    yText = dy / 2
    hText = ax.text(xText, yText, text, va="center", ha="left")

    # -- turn off the boundaries
    if not showAxBnd:
        ax.set_axis_off()
        ax.set_xticks([])
        ax.set_xticks([])

    return hLine, hText, ax


def _get_line_data(
    ax: Axes,
    x: Iterable | float,
    y: Iterable | float,
    u: Iterable | float,
    v: Iterable | float,
    config: VectorConfig = VectorConfig(),
) -> np.ndarray:
    x0, y0, dx, dy = _handle_dimensinons(x, y, u, v, config.skip)
    del x, y, u, v

    # change the default parameters from None to the estimation
    config._aspect = _get_aspect(ax)

    if config.scale is None:
        config.scale = _guess_scale(x0, y0, dx, dy)

    if config.headLenMax is None:
        config.headLenMax = _guess_headLenMax(
            dx, dy, config.rHeadLen, config.headAngle, config.scale
        )

    amps = np.absolute(dx + dy * 1j)
    angs = np.angle(dx + dy * 1j)

    bodyMults = 1 / config.scale
    deltaBody = bodyMults * np.array(
        (
            dx,
            dy * config._aspect,
        )
    )

    leftAngs = angs - (180 - config.headAngle) / 180 * np.pi
    rightAngs = angs + (180 - config.headAngle) / 180 * np.pi

    bodyLengths = np.absolute(deltaBody[0] + deltaBody[1] * 1j)
    headLengths = bodyLengths * config.rHeadLen / np.cos(config.headAngle / 180 * np.pi)
    headLengths[(headLengths > config.headLenMax)] = config.headLenMax

    deltaLeft = headLengths * np.array(
        (
            np.cos(leftAngs),
            np.sin(leftAngs) * config._aspect,
        )
    )
    deltaRight = headLengths * np.array(
        (
            np.cos(rightAngs),
            np.sin(rightAngs) * config._aspect,
        )
    )

    if config.pivot in ("tail"):
        moveback = 0
    elif config.pivot in ("middle", "center"):
        moveback = 0.5
    elif config.pivot in ("head"):
        moveback = 1
    else:
        raise NotImplementedError(f"{config.pivot=}")

    tails = np.array(
        (
            x0 - moveback * deltaBody[0],
            y0 - moveback * deltaBody[1],
        )
    )

    nans = np.nan * np.ones((2, len(x0)))

    data = np.stack(
        (
            tails,
            tails + deltaBody,
            tails + deltaBody + deltaLeft,
            nans,
            tails + deltaBody,
            tails + deltaBody + deltaRight,
            nans,
        ),
        axis=0,
    )

    # swap the dimension to [x/y, gridPoints, arrowPoints]
    data = np.swapaxes(data, 0, 1)
    data = np.swapaxes(data, 1, 2)

    return data


def _get_aspect(ax: Axes) -> float:
    if ax.get_autoscalex_on() or ax.get_autoscaley_on():
        raise NotImplementedError("xlim and ylim must be set to get the correct aspect")

    xfig, yfig = ax.figure.get_size_inches()  # ty: ignore
    axBox = ax.get_position()
    rxax, ryax = axBox.width, axBox.height

    xlim = ax.get_xlim()
    ylim = ax.get_ylim()

    xdraw = xlim[1] - xlim[0]
    ydraw = ylim[1] - ylim[0]

    xapparent = xfig * rxax / xdraw
    yapparent = yfig * ryax / ydraw

    return xapparent / yapparent


def _create_ax(
    ax: Axes,
    anchor: Literal["tr", "tl", "br", "bl"],
    quadrant: Literal[1, 2, 3, 4],
    rdx: float,
    rdy: float,
    anchorShift: tuple[float, float],  # units: relative to the new axes
) -> Axes:
    if anchor not in ("tr", "tl", "br", "bl"):
        raise ValueError(f"unrecognized {anchor=}")

    if quadrant not in (1, 2, 3, 4):
        raise ValueError(f"unrecognized {quadrant=}")

    parentPos = ax.get_position()
    X0, Y0, DX, DY = parentPos.x0, parentPos.y0, parentPos.width, parentPos.height
    X1 = X0 + DX
    Y1 = Y0 + DY

    dx = DX * rdx
    dy = DY * rdy

    ya = Y1 if anchor[0] == "t" else Y0
    xa = X1 if anchor[1] == "r" else X0

    if quadrant == 1:
        x0 = xa
        y0 = ya
    elif quadrant == 2:
        x0 = xa - dx
        y0 = ya
    elif quadrant == 3:
        x0 = xa - dx
        y0 = ya - dy
    elif quadrant == 4:
        x0 = xa
        y0 = ya - dy

    newax = ax.figure.add_axes(
        (
            x0 + anchorShift[0] * dx,
            y0 + anchorShift[1] * dy,
            dx,
            dy,
        )
    )
    return newax


def _handle_dimensinons(
    x: Iterable | float,
    y: Iterable | float,
    u: Iterable | float,
    v: Iterable | float,
    skip: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """return x, y, u, v"""
    x = np.asarray(x)
    y = np.asarray(y)
    u = np.asarray(u)
    v = np.asarray(v)

    # -- check dimensions (0, 1, 2d)
    if x.ndim >= 3 or y.ndim >= 3 or u.ndim >= 3 or v.ndim >= 3:
        raise ValueError(
            f"ndim <= 2 but found ndim(x, y, u, v) = {(x.ndim, y.ndim, u.ndim, v.ndim)}"
        )

    if x.ndim != y.ndim:
        raise ValueError(f"ndim(x, y) must equal but found {(x.ndim, y.ndim)} ")

    if u.ndim != v.ndim:
        raise ValueError(f"ndim(u, v) must equal but found {(u.ndim, v.ndim)} ")

    if x.ndim == 2:
        assert x.shape == y.shape

    assert u.shape == v.shape

    if (x.ndim, u.ndim) == (1, 2):
        assert u.shape == (len(y), len(x))
        x, y = np.meshgrid(x, y)
        x = x.ravel()[::skip]
        y = y.ravel()[::skip]
        u = u.ravel()[::skip]
        v = v.ravel()[::skip]
        return x, y, u, v

    if (x.ndim, u.ndim) == (1, 1):
        assert len(u) == len(x)
        x = x.ravel()[::skip]
        y = y.ravel()[::skip]
        u = u.ravel()[::skip]
        v = v.ravel()[::skip]
        return x, y, u, v

    if (x.ndim, u.ndim) == (0, 0):
        x = np.asarray([x])
        y = np.asarray([y])
        u = np.asarray([u])
        v = np.asarray([v])
        return x, y, u, v

    raise NotImplementedError(
        f"unable to handle ndim(x, y, u, v) = {(x.ndim, y.ndim, u.ndim, v.ndim)}"
    )


def _guess_scale(x, y, u, v) -> float:
    MAGIC_NUM = 1.2
    amp = _get_characteristic_amp(u, v)

    # estimate the density of vectors
    dx = np.nanmax(x) - np.nanmin(x)
    dy = np.nanmax(y) - np.nanmin(y)
    if dx == 0 and dy == 0:
        dxdy = 1
    elif dx == 0:
        dxdy = dy
    elif dy == 0:
        dxdy = dx
    else:
        dxdy = dx * dy

    density = np.sqrt(len(u) / dxdy)

    return density * amp * MAGIC_NUM


def _guess_headLenMax(u, v, rHeadLen, headAngle, scale) -> float:
    amp = _get_characteristic_amp(u, v)
    # divided by the cosine for tilting, and multiplied by the characteristic amplitude
    return rHeadLen / np.cos(headAngle / 180 * np.pi) * amp / scale


def _get_characteristic_amp(u, v) -> float:
    MAGIC_PERCENTILE = 80
    return np.sqrt(np.nanpercentile(u**2 + v**2, MAGIC_PERCENTILE))
