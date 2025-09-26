import numpy  as np


def lonlat2dxdy(lon: np.ndarray | list, lat:np.ndarray | list, R: int | float=6378_000) -> tuple[np.ndarray, np.ndarray]:
    '''
    calculates the zonal and meridional distances with 
        lon[ny, nx] (deg) or lon[nx]
        lat[ny, nx] (deg)    lat[ny]
        R as radius

    returns 
        dx[ny, nx], dy[ny, nx]
    '''
    #
    # ---- check inputs
    if isinstance(lon, (int, list)):
        lon = np.array(lon)

    if isinstance(lat, (int, list)):
        lat = np.array(lat)

    if not (
        (lon.ndim == lat.ndim and lon.ndim in [1, 2]) or
        (lon.ndim == 0 and lat.ndim == 1) or
        (lat.ndim == 0 and lon.ndim == 1)
    ):
        raise ValueError(f'input lon and lat must have 1 or 2d')

    #
    # ---- deg to rad
    piOver180 = np.pi / 180
    lon = np.float32(lon) * piOver180
    lat = np.float32(lat) * piOver180

    #
    # ---- make 2d
    if lon.ndim != 2:
        lon, lat = np.meshgrid(lon, lat)

    if lon.shape[-1] > 1:
        dlon = np.gradient(lon, axis=-1)
    else:
        dlon = np.zeros_like(lon)

    if lat.shape[-2] > 1:
        dlat = np.gradient(lat, axis=-2)
    else:
        dlat = np.zeros_like(lat)

    dx = R * np.cos(lat) * dlon
    dy = R * dlat

    return dx, dy


def lonlat2area(lon: np.ndarray | list, lat:np.ndarray | list, R: int | float=6378_000):
    dx, dy = lonlat2dxdy(lon, lat, R)
    return dx * dy


def lonlat2xy(lon, lat):
    dx, dy = lonlat2dxdy(lon, lat)
    if dx.shape[-1] > 1:
        x = np.cumsum(dx, axis=-1)
    else:
        x = np.zeros_like(dx)

    if dy.shape[-2] > 1:
        y = np.cumsum(dy, axis=-2)
    else:
        y = np.zeros_like(dy)
    return x, y


def uv2div(
    u: np.ndarray, 
    v: np.ndarray, 
    lon: np.ndarray, 
    lat: np.ndarray, 
    sumxy: bool = True,
    R: int | float = 6378_000,
) -> np.ndarray:
    dx, dy = lonlat2dxdy(lon, lat, R)
    udx = np.gradient(u, axis=-1) / dx
    vdy = np.gradient(v, axis=-2) / dy
    if sumxy:
        return udx + vdy
    else:
        return udx, vdy
