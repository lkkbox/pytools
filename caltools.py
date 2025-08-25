import numpy as np


def conform_axis(data1, data2, dims1, dims2, axis):
    dim1 = list(dims1[axis])
    dim2 = list(dims2[axis])
    dimShared = [d for d in dim1 if d in dim2]
    dims1[axis] = np.array(dimShared)

    # get the index for each data
    ind1 = [dim1.index(d) for d in dimShared]
    ind2 = [dim2.index(d) for d in dimShared]

    # extract the indices of each data
    data1 = np.swapaxes(data1, 0, axis)
    data2 = np.swapaxes(data2, 0, axis)
    data1 = data1[ind1, :]
    data2 = data2[ind2, :]
    data1 = np.swapaxes(data1, 0, axis)
    data2 = np.swapaxes(data2, 0, axis)

    return data1, data2, dims1


def centraldiff(data:np.ndarray, axis:int):
    data = np.swapaxes(data, 0, axis)
    data = np.concatenate(
        (
            (data[1, :] - data[0, :])[None, :],
            (data[2:, :] - data[0:-2, :])/2,
            (data[-1, :] - data[-2, :])[None, :]
        ),
        axis=0 
    )
    data = np.swapaxes(data, 0, axis)
    return data


def nearest_nice_number(inputs, targets=None, round_decimal=6):
    if targets is None:
        targets = [1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 9, 10]

    sign = np.sign(inputs)
    inputs = np.abs(inputs)
    
    targets = np.array(targets)
    inputs = np.array(inputs)

    log_inputs = np.log10(inputs)
    powers, residuals = divmod(log_inputs, 1)
    residuals = 10 ** residuals
    indices = np.argmin(np.abs([r - targets for r in residuals]), axis=-1)
    outputs = [
        round(targets[index] * 10 ** int(power), int(-power+round_decimal))
        for index, power in zip(indices, powers)
    ]
    outputs = outputs * sign

    outputs = [int(output) if output % 1 == 0 else output for output in outputs]

    return outputs


def fillNans2d(data, numSmooths, nsmooths=(3, 3), dims=(-1, -2)):
    data = np.array(data)
    mask = np.isnan(data)

    smoothed = data.copy()

    # fill the nans with zonal mean
    for iy in range(data.shape[dims[1]]):
        mean = np.nanmean(data[iy, :])
        smoothed[iy, np.isnan(data[iy, :])] = mean

    # fill the sill nans with the nearest meridional value
    for ix in range(data.shape[dims[0]]):
        smoothed[:, ix] = fill_nan_nearest(smoothed[:, ix])


    for i in range(numSmooths):
        smoothed = smooth(smoothed, nsmooths[0], dims[0])
        smoothed = smooth(smoothed, nsmooths[1], dims[1])

    data[mask] = smoothed[mask]
    return data


def fill_nan_nearest(arr, axis=-1):
    from scipy import interpolate
    nans = np.isnan(arr)
    x = np.arange(len(arr))
    f = interpolate.interp1d(x[~nans], arr[~nans], kind='nearest', 
                             fill_value="extrapolate", axis=axis)
    return f(x)


def lonlat2dxdy(lon, lat, R=6378_000):
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


def lonlat2area(lon, lat):
    dx, dy = lonlat2dxdy(lon, lat)
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


def grid2weight_1d(grid):
    delta = np.diff(grid)
    weight = [delta[0]/2, *((delta[:-1]+delta[1:])/2), delta[-1]/2]
    return np.array(weight)


def bootstrapResampling(data, numSamples, axis=0):
    data = np.swapaxes(data, 0, axis)
    newData = np.nan * np.ones((numSamples, *data.shape[1:]))
    lenDim = data.shape[0]
    indices = np.random.randint(0, lenDim, lenDim*numSamples)
    indices = np.reshape(indices, (numSamples, lenDim))
    for i in range(numSamples):
        newData[i, :] = np.nanmean(data[indices[i, :], :], axis=0)
    return np.swapaxes(newData, 0, axis)


def bootstrapPR(data, numSamples, prs, axis=0):
    data = np.swapaxes(data, 0, axis)
    boots = bootstrapResampling(data, numSamples)
    dprs = np.percentile(boots, prs, axis=0)
    return dprs


def bootstrapResampledDifferenceLevel(data1, data2, numSamples, axis=0):
    resampledData1 = bootstrapResampling(data1, numSamples, axis)
    resampledData2 = bootstrapResampling(data2, numSamples, axis)
    return np.nansum((resampledData1 > resampledData2), axis)/numSamples


def bootstrapResampledDifferenceLevelConst(data1, const, numSamples, axis=0):
    resampledData1 = bootstrapResampling(data1, numSamples, axis)
    return np.nansum((resampledData1 > const), axis)/numSamples


def smooth(dataArray, numSmooths, axis=0, **kwargs):
    from scipy.ndimage import uniform_filter1d
    isnan = np.isnan(dataArray)
    if not np.any(isnan):
        output = uniform_filter1d(
            dataArray, numSmooths, axis, mode='nearest', **kwargs
        )
        return output

    # deal with nans
    mean = np.nanmean(dataArray, keepdims=True, axis=axis)
    dataArray -= mean
    dataArray[isnan] = 0.
    output = uniform_filter1d(
        dataArray, numSmooths, axis, mode='nearest', **kwargs
    )
    output += mean
    output[isnan] = np.nan
    return output

# def nanSmooth(dataArray, numSmooths, axis=0, **kwargs):
#     from scipy.ndimage import uniform_filter1d
#     isnan = np.isnan(dataArray)
#     dataArray[isnan] = 0
#     dataArray = uniform_filter1d(
#         dataArray, numSmooths, axis, mode='nearest', **kwargs
#     )
#     dataArray[isnan] = np.nan
#     return dataArray


def getContinuousIntegersIntervals(inputList):
    if len(inputList) == 0:
        return [[]]

    if len(inputList) == 1:
        return [[inputList[0], inputList[0]]]

    breakers = []
    for d1, d2 in zip(inputList, inputList[1:]):
        if d2 == d1 + 1:
            continue
        breakers.append([d1, d2])

    if not breakers:
        return [[inputList[i] for i in [0, -1]]]

    intervals = [[inputList[0], breakers[0][0]]]
    for breaker1, breaker2 in zip(breakers, breakers[1:]):
        intervals.append([breaker1[1], breaker2[0]])

    intervals.append([breakers[-1][-1], inputList[-1]])
    return intervals


def mirror(levels):
    levels = list(levels)
    neg_levels = [-l for l in levels if l != 0]
    levels.extend(neg_levels)
    levels.sort()
    return levels


def w2g(LON, lon_s, lon_e):
    if lon_s is None:
        lon_s = -np.inf
    if lon_e is None:
        lon_e = np.inf

    if lon_s <= lon_e:
        indices = np.where(np.logical_and(lon_s <= LON, LON <= lon_e))
    else:
        indices = np.where(np.logical_or(lon_s <= LON, LON <= lon_e))

    indices = indices[0]

    if len(indices) == 0:
        print(
            f'[w2g] warning, no values are found, [xs, xe] = {lon_s, lon_e}, minMax(LON)=({np.min(LON)}, {np.max(LON)})')
        xs, xe = None, None
    elif len(indices) == 1:
        [xs, xe] = indices[[0, 0]]
    else:
        [xs, xe] = indices[[0, -1]]

    if xe is not None:
        xe = xe + 1  # for python indexing

    lon = LON[xs:xe]
    nx = len(lon)
    return xs, xe, nx, lon


def value2Slice(valueList, valueStart, valueEnd):
    #
    # ---- checking inputs ---- #
    if not isinstance(valueList, (list, np.ndarray)):
        raise TypeError('"valueList" must be a list.')

    valueList = list(valueList)

    for valueSmall, valueBig in zip(valueList, valueList[1:]):
        if valueSmall >= valueBig:
            raise ValueError(
                'values in "valueList" must be strictly increasing. '
                f'({valueSmall=}, {valueBig=})'
            )

    if valueStart is None:
        valueStart = -np.inf
    if valueEnd is None:
        valueEnd = np.inf

    if not isinstance(valueStart, (int, float)):
        raise TypeError('"valueStart" must be an integer of float')
    if not isinstance(valueEnd, (int, float)):
        raise TypeError('"valueEnd" must be an integer of float')

    if valueStart > valueEnd:
        raise ValueError(
            f'Inquiring with {valueStart=} > {valueEnd=} makes no sense.'
        )
    if valueStart > valueList[-1]:
        raise ValueError(
            f'The inquired "valueStart" is larger than the entire list: '
            f'{valueStart=} > {valueList[-1]=}'
        )
    if valueEnd < valueList[0]:
        raise ValueError(
            f'The inquired "valueEnd" is smaller than the entire list: '
            f'{valueEnd=} < {valueList[0]=}'
        )
    # TODO: is the element numeric?
    # for e in valueList:
    #     if not isinstance(e, (int, float)):
    #         raise TypeError('values in "valueList" must be integers or float.')

    #
    # ---- get sliceStart and sliceEnd ----
    for sliceStart, value in enumerate(valueList):
        if value >= valueStart:
            break
    for reversedSliceEnd, value in enumerate(valueList[::-1]):
        if value <= valueEnd:
            break

    return slice(sliceStart, len(valueList)-reversedSliceEnd)


def interp_1d(x, y, x_new, axis=0, extrapolate=False):
    '''
    This function interpolates the nd-array y(x) to y(x_new)
    along the left-most axis.
    x is an 1-d array, with the same length as the first dimension 
    of y.
    '''
    def strictly_increasing(L): return all(e1 < e2 for e1, e2 in zip(L, L[1:]))

    x = np.array(x, dtype=np.double)
    y = np.array(y, dtype=np.double)
    x_new = np.array(x_new, dtype=np.double)

    if np.array_equal(x, x_new):  # no need to interpolate
        return y

    if axis != 0:
        y = np.swapaxes(y, 0, axis)
    if x.ndim > 1:
        raise Exception(f'x.ndim must be 1 but input is {x.ndim}')
    if x_new.ndim > 1:
        raise Exception(f'x_new.ndim must be 1 but input is {x_new.ndim}')
    if len(x) != y.shape[0]:
        raise Exception(f'len(x) must be the same as y.shape[0]')
    if not strictly_increasing(x):
        raise Exception('x must be strictly increasing.')
    if not strictly_increasing(x_new):
        raise Exception('x_new must be strictly increasing.')
    if not extrapolate and np.min(x_new) < np.min(x):
        raise Exception(
            f'min(x_new) must >= min(x) but they are {np.min(x_new)}, {np.min(x)}')
    if not extrapolate and np.max(x_new) > np.max(x):
        raise Exception(
            f'max(x_new) must <= max(x) but they are {np.max(x_new)}, {np.max(x)}')

    nx = len(x)
    nx_new = len(x_new)

    # find index of x to interpolate
    ixl = np.zeros((nx_new,), dtype=np.int32)
    ixr = np.zeros((nx_new,), dtype=np.int32)

    for ix_new in range(nx_new):
        dx = np.array(x_new[ix_new] - x)

        if extrapolate:
            if x_new[ix_new] < x[0]:
                ixl[ix_new] = 0
                continue
            if x_new[ix_new] > x[-1]:
                ixl[ix_new] = nx - 2
                continue

        # check the exact same grid
        ix = np.where(dx == 0)[0]
        if len(ix) and ix == 0:
            ixl[ix_new] = ix
            continue
        if len(ix) and ix != 0:
            ixl[ix_new] = ix-1
            continue

        # find the intersection
        ix = np.where(dx < 0)[0][0]
        ixl[ix_new] = ix-1

    ixr = ixl + 1

    # interpolation to y_new
    y_new = x_new - x[ixl]
    y_new /= x[ixr] - x[ixl]

    y_new = np.tile(y_new, [1 for i in range(y.ndim)])  # for broadcasting
    if y_new.ndim != 1:
        y_new = np.swapaxes(y_new, 0, y_new.ndim-1)  # for broadcasting

    y_new = y_new * (y[ixr, :] - y[ixl, :])
    y_new += y[ixl]

    if axis != 0:
        y_new = np.swapaxes(y_new, 0, axis)
    return y_new


def scores_2d(forecast, observation, lat):
    def rmse():
        rmse = (forecast-observation)**2
        rmse = np.nanmean(rmse, axis=(-1, -2), keepdims=True)
        rmse = np.sqrt(rmse)
        rmse = np.nanmean(rmse, axis=-3)
        return np.squeeze(rmse)

    def pcc2():
        up = forecast * observation
        up = np.nansum(up, axis=(-1, -2), keepdims=True)
        down = np.sqrt(np.nansum(forecast**2, axis=(-1, -2), keepdims=True))
        down *= np.sqrt(np.nansum(observation**2,
                        axis=(-1, -2), keepdims=True))
        pcc = np.nanmean(up/down, axis=-3)
        return np.squeeze(pcc)

    def acc2():
        up = forecast * observation
        up = np.nansum(up, axis=-3, keepdims=True)
        down = np.sqrt(np.nansum(forecast**2, axis=-3, keepdims=True))
        down *= np.sqrt(np.nansum(observation**2, axis=-3, keepdims=True))
        acc = np.nanmean(up/down, axis=(-1, -2))
        return np.squeeze(acc)

    weight = np.sqrt(np.cos(lat / 180 * np.pi))
    weight = np.transpose(np.tile(weight, (1, 1)))
    forecast = np.array(forecast) * weight
    observation = np.array(observation) * weight

    return rmse(), pcc2(), acc2()


def harmonicFitting(x, y, nHarmList, axis=0):
    # Calculate the harmonic fitting for y to x (in radians) in the
    # n-th harmonic orders in nHarmList
    # mask = np.logical_not( np.logical_or( np.isnan( x), np.isnan(y)))

    if not isinstance(x, np.ndarray):
        x = np.array(x)
    x = np.squeeze(x)
    if x.ndim != 1:
        raise ValueError(f'only support x.ndim = 1 but {x.shape=}')
    if not isinstance(y, np.ndarray):
        y = np.array(y)
    if x.size != y.shape[axis]:
        raise ValueError(
            f'x ({x.size}) and y ({y.shape[axis]}) have inconsistent length at {axis=}')

    # ===========================================
    # permute axes
    y = np.swapaxes(y, axis, 0)
    x = np.tile(x, (1 for __ in range(y.ndim)))
    x = np.swapaxes(x, -1, 0)

    # ===========================================
    # begin
    yHat = np.repeat(np.nanmean(y, axis=0, keepdims=True), len(x), axis=0)

    for nHarm in nHarmList:
        c = np.nanmean(y * np.exp(-1j * x * nHarm), axis=0)
        amp = 2 * np.absolute(c)
        phase = np.angle(c)
        yHat += amp * np.cos(nHarm * x + phase)

    # ===========================================
    # inverse permuting axes
    yHat = np.swapaxes(yHat, 0, axis)

    return yHat


def bandPassFilter(data, freq_low, freq_high, sampling_frequency=1, axis=0):
    data = np.swapaxes(data, axis, -1)
    # Perform FFT on the data
    fft_data = np.fft.fft(data, axis=-1)
    frequencies = np.fft.fftfreq(data.shape[-1], 1/sampling_frequency)

    # Create a frequency mask to keep only the frequencies within the band-pass range
    mask = (np.abs(frequencies) >= freq_low) & (
        np.abs(frequencies) <= freq_high)

    # Apply the mask to the FFT data
    filtered_fft_data = fft_data * mask

    # Perform the inverse FFT to get the filtered signal back in the time domain
    filtered_data = np.fft.ifft(filtered_fft_data, axis=-1)

    filtered_data = np.swapaxes(filtered_data, axis, -1)
    return filtered_data


def smoothNans1d(data, axis):
    data = np.swapaxes(data, axis, 0)

    mask = np.isnan(data)
    smoothData = np.copy(data)
    smoothData[1:-1, :] = np.nanmean(
        np.concatenate(
            (data[None, :-2, :], data[None, 2:, :]), axis=0
        ),
        axis=0
    )

    data[mask] = smoothData[mask]

    data = np.swapaxes(data, axis, 0)
    return data
