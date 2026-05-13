from matplotlib.lines import Line2D
from typing import Literal
from matplotlib.axes import Axes
import numpy as np
from dataclasses import dataclass
from typing import Iterable
from copy import copy


@dataclass
class VectorConfig:
    scale: float | None = None
    headAngle: float = 40  # degree
    pivot: Literal["tail", "center", "middle", "head"] = "tail"
    aspect: float | None = None  # ax ylim / xlim
    rHeadLen: float = 0.3  # normalized 0-1: 1 is as long as the vector body
    headLenMax: float | None = None
    skip: int = 1


def vector(
    ax: Axes,
    x: Iterable | float,
    y: Iterable | float,
    u: Iterable | float,
    v: Iterable | float,
    config: VectorConfig = VectorConfig(),
    *args,
    **kwargs,
) -> tuple[Line2D, VectorConfig]:
    x0, y0, dx, dy = _handle_dimensinons(x, y, u, v, config.skip)

    # change the default parameters from None to the estimation
    if config.scale is None:
        config.scale = guess_scale(x0, y0, dx, dy)

    if config.headLenMax is None:
        config.headLenMax = (
            config.rHeadLen / np.cos(config.headAngle / 180 * np.pi) / config.scale
        )

    if config.aspect is None:
        config.aspect = _get_aspect(ax)

    # if config.aspect is None:
    angs = np.angle(dx + dy * 1j)
    amps = np.absolute(dx + dy * 1j)
    leftAngs = angs - (180 - config.headAngle) / 180 * np.pi
    rightAngs = angs + (180 - config.headAngle) / 180 * np.pi

    bodyScales = amps / config.scale
    headLengths = (
        amps / config.scale * config.rHeadLen / np.cos(config.headAngle / 180 * np.pi)
    )
    headLengths[(headLengths > config.headLenMax)] = config.headLenMax

    deltaBody = np.array(
        (
            bodyScales * dx,
            bodyScales * dy * config.aspect,
        )
    )
    deltaLeft = np.array(
        (
            headLengths * np.cos(leftAngs),
            headLengths * np.sin(leftAngs) * config.aspect,
        )
    )
    deltaRight = np.array(
        (
            headLengths * np.cos(rightAngs),
            headLengths * np.sin(rightAngs) * config.aspect,
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
    data = np.swapaxes(data, 0, 1)
    data = np.swapaxes(data, 1, 2)

    hPlot = ax.plot(
        data[0].ravel(),
        data[1].ravel(),
        *args,
        **kwargs,
    )

    return hPlot, config


def guess_scale(x, y, u, v) -> float:
    MAGIC_NUM = 1.2
    amp = np.sqrt(np.nanmax(u**2 + v**2))

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


def vector_example(
    config: VectorConfig,
    parentAx: Axes,
    anchor: Literal["tr", "tl", "br", "bl"],
    quadrant: Literal[1, 2, 3, 4],
    rdx: float,
    rdy: float,
    magnitude: float,
    text: str,
    padStart: float = 0.1,
    padText: float = 0.1,
):
    ax = create_ax(parentAx, anchor, quadrant, rdx, rdy)

    parentXlim = parentAx.get_xlim()
    parentYlim = parentAx.get_ylim()

    dx = (parentXlim[1] - parentXlim[0]) * rdx
    dy = (parentYlim[1] - parentYlim[0]) * rdy
    ax.set_xlim(0, dx)
    ax.set_ylim(0, dy)

    x = padStart * dx
    y = dy / 2
    u = magnitude
    v = 0

    config = copy(config)
    config.pivot = "tail"

    print(x, y, u, v)
    print(config.scale, config.aspect)
    vector(ax, x, y, u, v, config)
    print(config.scale, config.aspect)


def _get_aspect(ax: Axes) -> float:
    if ax.get_autoscalex_on() or ax.get_autoscaley_on():  # ty: ignore
        raise NotImplementedError("xlim and ylim must be set before drawing")

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


def create_ax(
    ax: Axes,
    anchor: Literal["tr", "tl", "br", "bl"],
    quadrant: Literal[1, 2, 3, 4],
    rdx: float,
    rdy: float,
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

    newax = ax.figure.add_axes((x0, y0, dx, dy))  # ty: ignore
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

    assert x.shape == y.shape
    assert u.shape == v.shape

    if (x.ndim, u.ndim) == (1, 2):
        assert u.shape == (len(y), len(x))
        y, x = np.meshgrid(y, x)
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
