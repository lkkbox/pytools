import numpy as np
import os
import inspect
import colorsys
import matplotlib
import matplotlib.pyplot as plt
from ..caltools.caltools import interp_1d


def _get_ncl_cmap_dir():
    frame = inspect.stack()[0]
    module = inspect.getmodule(frame[0])

    assert module is not None
    fileName = module.__file__

    assert fileName is not None
    fileName = fileName.replace(r"/./", r"/")

    dirName = os.path.dirname(fileName)
    subDir = "ncl_colormaps"
    return f"{dirName}/{subDir}"


_NCL_FILE_EXTS = ("rgb", "gp", "ncmap")


def _get_valid_ncl_cmap_names():
    dirName = _get_ncl_cmap_dir()
    fileNames = os.listdir(dirName)
    return [
        f.split(".")[:-1][0] for f in fileNames if f.split(".")[-1] in _NCL_FILE_EXTS
    ]


_NCL_CMAP_DIR = _get_ncl_cmap_dir()
_CMAP_NAMES_MPL = matplotlib.colormaps()
_CMAP_NAMES_NCL = _get_valid_ncl_cmap_names()


def _get_mpl_cmap_colors(name: str, n: int) -> list[tuple[float, ...]]:
    if name not in _CMAP_NAMES_MPL:
        print(f"valid names: {_CMAP_NAMES_MPL}")
        raise ValueError(f"{name=} is not a valid MPL colormap name.")

    cmap = plt.get_cmap(name)
    return [cmap(value / (n - 1)) for value in range(n)]


def _get_ncl_cmap_colors(name: str, n: int) -> list[tuple[float, ...]]:
    if name not in _CMAP_NAMES_NCL:
        print(f"valid names: {_CMAP_NAMES_NCL}")
        raise ValueError(f"{name=} is not a valid NCL colormap name.")

    # find the correct file ext
    for ext in _NCL_FILE_EXTS:
        fileName = f"{_NCL_CMAP_DIR}/{name}.{ext}"
        if os.path.exists(fileName):
            break

    rgb0 = _read_ncl_cmap_file(fileName)
    hsv0 = [colorsys.rgb_to_hsv(r, g, b) for r, g, b in rgb0]

    x = np.linspace(0, 1, n)
    x0 = np.linspace(0, 1, len(rgb0))

    # hsv = interp_1d(x0, hsv0, x)
    # return [colorsys.hsv_to_rgb(h, s, v) for h, s, v in hsv]

    rgb = interp_1d(x0, rgb0, x)
    return rgb


def _read_ncl_cmap_file(fileName) -> list[tuple[float, ...]]:
    def get_numbers_if_valid(line):
        invalid = None

        if not all_are_num_space(line):
            return invalid

        numbers = line.split()
        numbers = [float(number) for number in numbers]

        if len(numbers) not in (3, 4):  # r, g, b
            return invalid

        if any([number > 255 for number in numbers]) or any(
            [number < 0 for number in numbers]
        ):
            return invalid

        return numbers

    def all_are_num_space(line):
        isNumSpace = [char not in " .0123456789" for char in line]
        if any(isNumSpace):
            return False
        return True

    with open(fileName, "r") as h:
        lines = h.read()

    rgbList = []
    for line in lines.split("\n"):
        numbers = get_numbers_if_valid(line)
        if numbers is None:
            continue
        rgbList.append(tuple(numbers))

    is255 = False
    for rgb in rgbList:
        for value in rgb:
            if value > 1:
                is255 = True
                break

    if is255:
        rgbList = [tuple(value / 255 for value in rgb) for rgb in rgbList]

    return rgbList


def get_cmap_colors(name: str, n: int) -> list[tuple[float, ...]]:
    if name in _CMAP_NAMES_MPL:
        return _get_mpl_cmap_colors(name, n)

    elif name in _CMAP_NAMES_NCL:
        colors = _get_ncl_cmap_colors(name, n)
        return colors

    else:
        print("valid names:")
        print(_CMAP_NAMES_MPL)
        print(_CMAP_NAMES_NCL)
        raise ValueError(f"unknown cmap {name=}")
