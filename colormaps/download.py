#!/nwpr/gfs/com120/.conda/envs/rd/bin/python
import os

def main():
    downloadRGB()


def downloadRGB():
    url = 'https://www.ncl.ucar.edu/Document/Graphics/ColorTables/Files/ncl_colormaps.tar'
    output = 'ncl_colormaps.tar'
    command = f'wget {url} -O {output}'
    os.system(command)


if __name__ == '__main__':
    main()