from dataclasses import dataclass
from typing import TypeAlias
from typing import Literal

from matplotlib.axes import Axes
from matplotlib.figure import Figure
from .shading import contourf2

fourFloats: TypeAlias = tuple[float, float, float, float]


def iax_to_irow_icol(iax: int, ncol: int) -> tuple[int, int]:
    """returns irow, icol"""
    irow = iax // ncol
    icol = iax % ncol
    return irow, icol


def draw_colorbar(
    ax: Axes,
    levels: list[float],
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
    tickLabels = [str(l) for l in levels]

    if orientation == "v":
        x, y = y, x
        z = list(zip(*z))

    contourf2(
        ax,
        x,
        y,
        z,
        levels,
        cmap,
        plotColorbar=False,
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

    # ax.tick_params(xOrY)


def add_subplot(
    fig: Figure,
    nrow: int,
    ncol: int,
    iax: int,
    xPad: float,
    yPad: float,
    figPads: fourFloats,
) -> Axes:
    return fig.add_subplot(
        nrow,
        ncol,
        iax + 1,
        position=get_subplot_position(
            nrow,
            ncol,
            iax,
            xPad,
            yPad,
            figPads,
        ),
    )


def get_subplot_position(
    nrow: int,
    ncol: int,
    iax: int,
    xPad: float,
    yPad: float,
    figPads: fourFloats,
) -> fourFloats:
    """
    return the position of a subplot with a nicer layout
    [left, bottom, width, height]

    parameter:
        figPads = right, left, bottom, top (clockwise)
    """

    # sanity check
    if not 0 <= iax < nrow * ncol:
        raise ValueError(f"invalid {iax=} for {(nrow,ncol)=}")

    irow, icol = iax_to_irow_icol(iax, ncol)

    # calculate the width and height of the panel
    allNumXPad = ncol - 1
    allNumYPad = nrow - 1
    width = (1 - allNumXPad * xPad - figPads[0] - figPads[2]) / ncol
    height = (1 - allNumYPad * yPad - figPads[1] - figPads[3]) / nrow

    # calculate the starting point of the panel
    left = figPads[2] + icol * (xPad + width)
    bottom = figPads[1] + (nrow - irow - 1) * (yPad + height)

    return (left, bottom, width, height)


def get_cbar_position(
    loc: Literal["l", "r", "b", "t"],
    ratio: float,
    figPads: fourFloats,
) -> fourFloats:
    """
    return the position of a colorbar with a nicer layout
           [left, bottom, width, height]

    parameter:
        ratio = 0 to 1 # the ratio to fill in the figPad
        loc = 'l', 'r', 'b', 't' for left, right, bottom, top
        figPads = right, left, bottom, top (clockwise)
    """

    if loc in ["l", "r"]:
        height = 1 - figPads[1] - figPads[3]
        y0 = figPads[1]
        if loc == "l":
            width = ratio * figPads[2]
            x0 = (1 - ratio) * figPads[2] / 2

        elif loc == "r":
            width = ratio * figPads[0]
            x0 = 1 - width - (1 - ratio) * figPads[0] / 2

    elif loc in ["b", "t"]:
        width = 1 - figPads[0] - figPads[2]
        x0 = figPads[2]
        if loc == "b":
            height = ratio * figPads[1]
            y0 = (1 - ratio) * figPads[1] / 2

        elif loc == "t":
            height = ratio * figPads[3]
            y0 = 1 - height - (1 - ratio) * figPads[3] / 2

    return (x0, y0, width, height)


def snap_position(
    ax: Axes,
    target: Axes,
    mode: Literal["h", "v", "both"],
) -> None:
    target_pos = target.get_position()
    source_pos = ax.get_position()

    if mode == "h":
        pos = (
            target_pos.x0,
            source_pos.y0,
            target_pos.width,
            source_pos.height,
        )
    elif mode == "v":
        pos = (
            source_pos.x0,
            target_pos.y0,
            source_pos.width,
            target_pos.height,
        )
    elif mode == "both":
        pos = (
            target_pos.x0,
            target_pos.y0,
            target_pos.width,
            target_pos.height,
        )

    ax.set_position(pos)


@dataclass
class Subplot:
    nx: int
    ny: int
    xPad: float | tuple[float, ...]
    yPad: float | tuple[float, ...]
    figPads: fourFloats
    """
    nx: int > 0
    ny: int > 0
    xPad: float | tuple[float, ...] 0-1
    yPad: float | tuple[float, ...] 0-1
    figPads: fourFloats 0-1
    """

    def __post_init__(self):
        self._xPads = self._get_pads(self.xPad, self.nx)
        self._yPads = self._get_pads(self.yPad, self.ny)
        self.width = self._cal_length(
            self._xPads, (self.figPads[0], self.figPads[2]), self.nx
        )
        self.height = self._cal_length(
            self._yPads, (self.figPads[1], self.figPads[3]), self.ny
        )

        self.axes: dict[int, tuple[Axes, fourFloats]] = {}

    def _register_axes(self, iax: int, ax: Axes, position: fourFloats) -> None:
        self.axes.update({iax: (ax, position)})

    def restore_positions(self) -> None:
        for iax, (ax, position) in self.axes.items():
            ax.set_position(position)

    def draw_colorbar(
        self,
        fig: Figure,
        iside: Literal[0, 1, 2, 3],
        levels: list[float],
        cmap: str,
        rdx: float,
        rdy: float,
        rxoffset: float = 0,
        ryoffset: float = 0,
    ) -> Axes:
        """
        fig: Figure,
        iside: Literal[0, 1, 2, 3],
        levels: list[float],
        cmap: str,
        rdx: float, 0-1
        rdy: float, 0-1
        """
        if iside in [1, 3]:
            orientation = "h"
        else:
            orientation = "v"

        ax = self.create_sided_ax(fig, iside, rdx, rdy, rxoffset, ryoffset)
        draw_colorbar(ax, levels, cmap, orientation)

        if iside == 0:
            ax.yaxis.tick_right()

        return ax

    def get_iax_position(
        self, iax: int
    ) -> tuple[
        float,
        float,
        float,
        float,
    ]:
        ix, iy = self._iax_to_ix_iy(iax)

        left = self.figPads[2]
        for i in range(ix):
            left += self._xPads[i] + self.width

        bottom = 1 - (self.figPads[3] + self.height)
        for i in range(iy):
            bottom -= self._yPads[i] + self.height
        return (left, bottom, self.width, self.height)

    def create_ax(self, fig: Figure, iax: int) -> Axes:
        position = self.get_iax_position(iax)
        ax = fig.add_subplot(position=position)
        self._register_axes(iax, ax, position)
        return ax

    def create_sided_ax(
        self,
        fig: Figure,
        iside: Literal[0, 1, 2, 3],
        rdx: float,
        rdy: float,
        rxoffset: float,
        ryoffset: float,
        keepOtherPads: bool = True,
    ) -> Axes:
        """
        fig: Figure,
        iside: Literal[0, 1, 2, 3],
        rdx: float, 0-1
        rdy: float, 0-1
        rxoffset: float, 0-1
        ryoffset: float, 0-1
        keepOtherPads: bool = True,
        """
        position = self.get_sided_position(iside, rdx, rdy, rxoffset, ryoffset)
        ax = fig.add_subplot(position=position)
        iax = iside + self.nx * self.ny
        self._register_axes(iax, ax, position)
        return ax

    def get_sided_position(
        self,
        iside: Literal[0, 1, 2, 3],
        rdx: float,
        rdy: float,
        rxoffset: float,
        ryoffset: float,
        keepOtherPads: bool = True,
    ) -> fourFloats:
        """
        iside: Literal[0, 1, 2, 3],
        rdx: float, 0-1
        rdy: float, 0-1
        rxoffset: float, 0-1
        ryoffset: float, 0-1
        keepOtherPads: bool = True,
        """
        if keepOtherPads:
            if iside in [0, 2]:
                canvasWidth = self.figPads[iside]
                canvasHeight = 1 - self.figPads[1] - self.figPads[3]
            else:
                canvasHeight = self.figPads[iside]
                canvasWidth = 1 - self.figPads[0] - self.figPads[2]
        else:
            if iside in [0, 2]:
                canvasWidth = self.figPads[iside]
                canvasHeight = 1
            else:
                canvasHeight = self.figPads[iside]
                canvasWidth = 1

        # normalize to figure unit
        width = rdx * canvasWidth
        height = rdy * canvasHeight
        padWidth = 0.5 * (1 - rdx) * canvasWidth
        padHeight = 0.5 * (1 - rdy) * canvasHeight
        xoffset = rxoffset * canvasWidth
        yoffset = ryoffset * canvasHeight

        if iside in [0, 1, 2]:
            bottom = padHeight
        elif iside == 3:
            bottom = 1 - padHeight - height

        if iside in [1, 2, 3]:
            left = padWidth
        elif iside == 0:
            left = 1 - padWidth - width

        if keepOtherPads:
            if iside in [0, 2]:
                bottom += self.figPads[1]
            elif iside in [1, 3]:
                left += self.figPads[2]

        return left + xoffset, bottom + yoffset, width, height

    @staticmethod
    def _get_pads(
        pads: float | tuple[float, ...], nPanels: int
    ) -> tuple[float, ...]:
        if isinstance(pads, (float, int)):
            return tuple([pads] * (nPanels - 1))

        if len(pads) == nPanels - 1:
            return pads

        raise ValueError(
            f"expected ncol-1 ({nPanels - 1}) elements in xPad but found {len(pads)}"
        )

    def _iax_to_ix_iy(self, iax: int) -> tuple[int, int]:
        """returns (ix, iy)"""
        if not 0 <= iax < self.nx * self.ny:
            raise ValueError(f"invalid {iax=} for (nx,ny)={(self.nx, self.ny)}")

        iy = iax // self.nx
        ix = iax % self.nx
        return ix, iy

    @staticmethod
    def _cal_length(
        panelPads: tuple[float, ...], figPads: tuple[float, float], nPanels: int
    ) -> float:
        blank = sum(panelPads) + sum(figPads)
        return (1 - blank) / nPanels
