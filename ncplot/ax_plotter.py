from . import reader
from .. import plottools as pt
from matplotlib.axes import Axes
from matplotlib.colors import Colormap

def contourf2(
    ax: Axes, 
    path: str, varname: str, minmaxs: list[list[float | int]], idimxy: list[int] | tuple[int], 
    clevs: list[int | float], cmap: str | Colormap='viridis', 
    plotColorbar: bool=True, cbarOptions: dict={},
    iDimT: int | None=None, decodeTime=True, nanmean=True
) -> None:
    data, dims = reader.read2d(path, varname, minmaxs, idimxy, iDimT, decodeTime, nanmean)
    pt.contourf2(
        ax, dims[-1], dims[-2], data, clevs, cmap, 
        plotColorbar=plotColorbar, cbarOptions=cbarOptions
    )

