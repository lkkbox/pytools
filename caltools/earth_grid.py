import numpy as np


def lonlat2dxdy(lon: np.ndarray | list, lat: np.ndarray | list, R: int | float = 6378_000) -> tuple[np.ndarray, np.ndarray]:
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


def lonlat2area(lon: np.ndarray | list, lat: np.ndarray | list, R: int | float = 6378_000):
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


def points_in_polygon(
    x_coords: np.ndarray,
    y_coords: np.ndarray,
    vertices: list[tuple[int | float, int | float]],
):
    """
    Returns a 2D boolean array indicating whether grid points are inside a polygon.

    Parameters
    ----------
    x_coords : (Nx,) array-like
        X coordinates of grid
    y_coords : (Ny,) array-like
        Y coordinates of grid
    vertices : list of (x, y)
        Polygon vertices [(x0,y0), (x1,y1), ..., (xn,yn)]

    Returns
    -------
    mask : (Ny, Nx) ndarray of bool
        True where (x, y) lies inside or on the polygon boundary
    """
    if x_coords.ndim != y_coords.ndim:
        raise ValueError(f'{x_coords.ndim=} but {y_coords.ndim=}')

    if x_coords.ndim > 2:
        raise ValueError(f'{x_coords.ndim=} is larger than 2')

    if x_coords.ndim == 2 and x_coords.shape != y_coords.shape:
        raise ValueError(f'{x_coords.shape=} but {y_coords.shape=}')

    if x_coords.ndim == 1:
        X, Y = np.meshgrid(x_coords, y_coords)
    else:
        X, Y = x_coords, y_coords

    verts = np.asarray(vertices)

    x = X.ravel()
    y = Y.ravel()

    xv = verts[:, 0]
    yv = verts[:, 1]
    n = len(verts)

    inside = np.zeros_like(x, dtype=bool)

    # Ray casting algorithm
    j = n - 1
    for i in range(n):
        xi, yi = xv[i], yv[i]
        xj, yj = xv[j], yv[j]

        intersect = (
            ((yi > y) != (yj > y)) &
            (x < (xj - xi) * (y - yi) / (yj - yi + 1e-15) + xi)
        )
        inside ^= intersect
        j = i

    return inside.reshape(Y.shape)


_pacificBndPoints = [
    [240, 90],
    [240, 50],
    [260, 20],
    [273, 15],
    [278, 8.5],
    [290, 8.5],
    [290, -50],
    [290, -90],
    [150, -90],
    [150, -50],
    [143, -10],
    [120, -7],
    [105, 0],
    [100, 10],
    [100, 50],
    [100, 90]
]


def is_in_pacific(lon: np.ndarray, lat: np.ndarray) -> np.ndarray[np.bool]:
    return points_in_polygon(lon, lat, _pacificBndPoints)
