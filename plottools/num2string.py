import numpy as np


def scientific_notation(
    number: float | int, 
    format_significand: str | None = None,
    format_power: str = 'd',
) -> str:
    log_number = np.log10(number)
    power = int(np.floor(log_number))
    significand = number / (10 ** power)

    if format_significand is not None:
        str_significand = f'{significand:{format_significand}}'
    else:
        str_significand = f'{significand}'

        # remove trailing zeros
        while str_significand[-1] == '0':
            str_significand = str_significand[:-1]

        # remove trailing dot
        if str_significand[-1] == '.':
            str_significand = str_significand[:-1]

    str_power = f'{power:{format_power}}'

    if str_significand == '1': # show powers only
        return fr'$10^{'{'}{str_power}{'}'}$'
    else:
        mult_character = r'$\times$'
        return fr'${str_significand}{mult_character}10^{'{'}{str_power}{'}'}$'


def str_lonlatbox(
    lonw: int|float, 
    lone: int|float, 
    lats: int|float, 
    latn: int|float, 
    joiner1: str = ',',
    joiner2: str = '-',
):
    str1 = f'{str_join(joiner1, str_lons([lonw, lone]))}'
    str2 = f'{str_join(joiner1, str_lats([lats, latn]))}'
    return str_join(joiner2, [str1, str2])


def str_lons(yticks):
    return [str_lon(ytick) for ytick in yticks]


def str_lats(yticks):
    return [str_lat(ytick) for ytick in yticks]


def str_lon(lon):
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


def str_lat(lat):
    if lat == 0:
        y, we = lat, f'{chr(176)}'
    if lat < 0:
        y, we = -lat, f'{chr(176)}S'
    if lat > 0:
        y, we = lat, f'{chr(176)}N'
    return str(y)+we
    

def str_join(joiner:str, elements:list[int|float|str]) -> str:
    return joiner.join([str(e) for e in elements])
