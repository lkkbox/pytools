import numpy as np
import os
import inspect
from matplotlib.colors import ListedColormap
from ..plottools import contourf2
from ..caltools import interp_1d
import colorsys


def example():
    colors = ['green', 'black', 'white', 'red', 'yellow']
    makeColorMap(colors, None, [-0.2, 1.2])


def example():
    import matplotlib.pyplot as plt
    from ..caltools import mirror

    levels = mirror([0.2, 0.4, 0.6, 0.8, 1, 1.5])
    colorName = 'matlab_hsv'
    colorName = 'precip_diff_12lev'
    cmap = nclColormap(colorName=colorName, numResampling=23)

    x = np.linspace(0, 2*np.pi, 100)
    y = np.linspace(0, 2*np.pi, 100)
    z = np.sin(2*x)[None, :] + np.sin(3*y)[:, None]

    fig, ax = plt.subplots()
    hcf, cbar = contourf2(ax, x, y, z, levels=levels, cmap=cmap, extend='both')
    # ax.contour(x, y, z, levels=levels, colors='grey', linestyles='-')
    # hcf = ax.contourf(
    #     x, y, z, levels=levels,
    #     cmap=cmap, extend='both', vmin=-1.8, vmax=1.8
    # )
    # fig.colorbar(hcf)
    fig.savefig('../messy/a.png')


def makeColorMap(colors0, numResampling=None, vRange=None):

    def extrapolateHSV():
        rgbs = [rgba[:-1] for rgba in colors0]
        hsvs0 = [colorsys.rgb_to_hsv(*rgb) for rgb in rgbs]
        hsvs1 = interp_1d(x0, hsvs0, x1, 0, True)
        rgbs1 = []
        for hsv in hsvs1:
            h, s, v = hsv

            while h > 1:
                h -= 1
            while h < 0:
                h += 1

            if s > 1:
                s = 1
            if s < 0:
                s = 0

            if v > 1:
                v = 1
            if v < 0:
                v = 0

            rgb = colorsys.hsv_to_rgb(h, s, v)
            rgbs1.append(rgb)

        return [[*rgb, 1] for rgb in rgbs1]

    if numResampling is None and vRange is None:
        return ListedColormap(colors0)

    if vRange is None:
        vRange = [0, 1]

    colors0 = ListedColormap(colors0).colors
    numColors0 = len(colors0)

    if numResampling is None:
        colorDensity = 1/numColors0
        numResampling = round((vRange[1] - vRange[0])/colorDensity)

    x0 = np.linspace(0,         1,         numColors0)
    x1 = np.linspace(vRange[0], vRange[1], numResampling)
    colors1 = extrapolateHSV()

    return ListedColormap(colors1)


def nclColormap(colorName='matlab_hsv', numResampling=None, vRange=None, reverse=False):

    def isValidColorName(colorName):
        dirName = _getNclDirectory()
        extensions = _getNclExtensions()
        fileNames = [f'{dirName}/{colorName}.{ext}' for ext in extensions]
        isValid = [os.path.exists(fileName) for fileName in fileNames]
        if not any(isValid):
            return False, None
        else:
            return True, fileNames[isValid.index(True)]

    def readFileRgb(fileName):

        def readLines():
            with open(fileName, 'r') as h:
                lines = h.read()
            return lines

        def getNumbersIfValid(line):

            invalid = None

            if not allAreNumSpace(line):
                return invalid

            numbers = line.split()
            numbers = [float(number) for number in numbers]

            if len(numbers) != 3:  # r, g, b
                return invalid

            if (
                    any([number > 255 for number in numbers])
                or any([number < 0 for number in numbers])
            ):
                return invalid

            return numbers

        def allAreNumSpace(line):
            isNumSpace = [char not in ' .0123456789' for char in line]
            if any(isNumSpace):
                return False
            return True

        rgbList = []
        lines = readLines().split('\n')
        for line in lines:
            numbers = getNumbersIfValid(line)
            if numbers is None:
                continue
            rgbList.append(numbers)

        return rgbList

    isValid, fileName = isValidColorName(colorName)
    if not isValid:
        raise ValueError(f'invalid {colorName=}')

    rgbList = np.array(readFileRgb(fileName))

    # 0-255 or 0-1 ?
    if np.all(np.mod(rgbList, 1) == 0):
        rgbList = [[e/255 for e in rgb] for rgb in rgbList]

    rgbaList = [[*rgb, 1] for rgb in rgbList]
    if reverse:
        rgbaList.reverse()

    cmap = makeColorMap(rgbaList, numResampling, vRange)
    return cmap


def getValidNclColorNames():
    dirName = _getNclDirectory()
    fileNames = os.listdir(dirName)
    return [
        f.split('.')[:-1][0] for f in fileNames
        if f.split('.')[-1] in _getNclExtensions()
    ]


def _getNclDirectory():
    frame = inspect.stack()[0]
    module = inspect.getmodule(frame[0])
    fileName = module.__file__
    fileName = fileName.replace(r'/./', r'/')
    dirName = os.path.dirname(fileName)
    subDir = 'ncl_colormaps'
    return f'{dirName}/{subDir}'


def _getNclExtensions():
    return ['rgb', 'gp', 'ncmap']
