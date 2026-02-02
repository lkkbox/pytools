import multiprocessing as mp
from numba import njit, prange
from ..terminaltools import FlushPrinter
import numpy as np

"""
module for calculating the statistics by the bootstrapping method
"""


@njit(parallel=True, cache=True)
def resampled_stat_numba(data, nboot):
    nsample = data.shape[0]

    # Get the shape of the features (everything after the first dimension)
    trailing_shape = data.shape[1:]

    # Calculate total number of elements in each bootstrap sample
    # Using np.prod is safer for Numba than dynamic unpacking
    n_features = 1
    for s in trailing_shape:
        n_features *= s

    # Flatten data for internal processing
    flat_data = data.reshape(nsample, n_features)

    # Pre-allocate output
    data_out = np.empty((nboot, n_features), dtype=data.dtype)

    for i in prange(nboot):
        # Local random state for each thread
        indices = np.random.randint(0, nsample, nsample)

        for j in range(n_features):
            summ = 0.0
            count = 0
            for idx in indices:
                val = flat_data[idx, j]
                if not np.isnan(val):
                    summ += val
                    count += 1

            data_out[i, j] = summ / count if count > 0 else np.nan

    # CRITICAL FIX: Construct the final shape explicitly
    # Numba prefers building a tuple rather than using * unpacking
    final_shape = (nboot,) + trailing_shape
    return data_out.reshape(final_shape)


@njit(parallel=True, cache=True)
def resampled_stat_numba_multiprocess(
    queue: mp.Queue, data: np.ndarray, nboot: int
) -> None:
    nsample = data.shape[0]

    # Get the shape of the features (everything after the first dimension)
    trailing_shape = data.shape[1:]

    # Calculate total number of elements in each bootstrap sample
    # Using np.prod is safer for Numba than dynamic unpacking
    n_features = 1
    for s in trailing_shape:
        n_features *= s

    # Flatten data for internal processing
    flat_data = data.reshape(nsample, n_features)

    # Pre-allocate output
    data_out = np.empty((nboot, n_features), dtype=data.dtype)

    for i in prange(nboot):
        # Local random state for each thread
        indices = np.random.randint(0, nsample, nsample)

        for j in range(n_features):
            summ = 0.0
            count = 0
            for idx in indices:
                val = flat_data[idx, j]
                if not np.isnan(val):
                    summ += val
                    count += 1

            data_out[i, j] = summ / count if count > 0 else np.nan

    # CRITICAL FIX: Construct the final shape explicitly
    # Numba prefers building a tuple rather than using * unpacking
    final_shape = (nboot,) + trailing_shape
    # queue.put(data_out.reshape(final_shape))


def diff_level(
    data1: np.ndarray,
    data2: np.ndarray,
    nboot: int,
    axis: int = 0,
    batchsize: int | None = None,
) -> np.ndarray:
    if batchsize is None:
        batchsize = nboot

    if nboot % batchsize != 0:
        raise ValueError(f"{nboot=} % {batchsize=} is not zero")

    nbatch = int(nboot / batchsize)

    data1 = np.swapaxes(data1, 0, axis)
    data2 = np.swapaxes(data2, 0, axis)

    dataOut = np.zeros(data1.shape[1:])

    fp = FlushPrinter()
    for i in range(nbatch):
        fp.flush(f"diff_level: {i} / {nbatch}")
        resampled1 = resampled_stat_numba(data1, batchsize)
        resampled2 = resampled_stat_numba(data2, batchsize)
        dataOut += np.nansum((resampled1 > resampled2), axis) / nboot

    return dataOut


def diff_level_new(
    data1: np.ndarray,
    data2: np.ndarray,
    nboot: int,
    axis: int = 0,
    batchsize: int | None = None,
) -> np.ndarray:
    if batchsize is None:
        batchsize = nboot

    if nboot % batchsize != 0:
        raise ValueError(f"{nboot=} % {batchsize=} is not zero")

    nbatch = int(nboot / batchsize)

    data1 = np.swapaxes(data1, 0, axis)
    data2 = np.swapaxes(data2, 0, axis)

    dataOut = np.zeros(data1.shape[1:])

    q = mp.Queue()
    fp = FlushPrinter()
    for i in range(nbatch):
        fp.flush(f"diff_level: {i} / {nbatch}")
        p = mp.Process(
            target=resampled_stat_numba_multiprocess,
            args=(
                q,
                data1,
                batchsize,
            ),
        )
        resampled1 = q.get()
        p.start()
        p.join()

        p = mp.Process(
            target=resampled_stat_numba_multiprocess,
            args=(
                q,
                data2,
                batchsize,
            ),
        )
        resampled2 = q.get()
        p.start()
        p.join()

        dataOut += np.nansum((resampled1 > resampled2), axis) / nboot

    return dataOut


# def percentile(
#     datas_in: list[np.ndarray],
#     stat_func: Callable,
#     n_boot: int,
#     prs: list[int|float],
# ):
#     '''
#     calculate the percentiles of resampled stats
#     '''
#     checkType(datas_in, list, 'datas_in')
#     checkType(stat_func, Callable, 'stat_func')
#     checkType(n_boot, int, 'n_boot')
#     checkType(prs, list, 'prs')
#     for data in datas_in:
#         checkType(data, np.ndarray, 'elements in datas_in')
#     for pr in prs:
#         checkType(pr, [list, int], 'elements in prs')
#
#     boots = resampled_stat(datas_in, stat_func, n_boot)
#     return np.percentile(boots, prs, axis=0)
#
#


#
#
# def diff_level_const(
#     datas_in: list[np.ndarray],
#     const: float | int,
#     stat_func: Callable,
#     n_boot: int,
# ):
#     resampled = resampled_stat(datas_in, stat_func, n_boot)
#     return np.nansum((resampled > const), 0) / n_boot
#
#
#
# def bootstrapResampledDifferenceLevel(data1, data2, numSamples, axis=0):
#     resampledData1 = bootstrapResampling(data1, numSamples, axis)
#     resampledData2 = bootstrapResampling(data2, numSamples, axis)
#     return np.nansum((resampledData1 > resampledData2), axis)/numSamples
#
#
# def bootstrapResampledDifferenceLevelConst(data1, const, numSamples, axis=0):
#     resampledData1 = bootstrapResampling(data1, numSamples, axis)
#     return np.nansum((resampledData1 > const), axis)/numSamples
#
# def resampled_stat(queue, data, nboot, axis=0):
#     # Move the axis to the front
#     if axis != 0:
#         data = np.swapaxes(data, 0, axis)
#
#     # Ensure data is C-contiguous for Numba performance
#     if not data.flags.c_contiguous:
#         data = np.ascontiguousarray(data)
#
#     result = resampled_stat_numba(data, nboot)
#
#     # Move the axis back
#     if axis != 0:
#         result = np.swapaxes(result, 0, axis)
#
#     return result
#
#
# def resampled_stat_nonnumba(
#     data: np.ndarray,
#     nboot: int,
#     axis: int = 0,
#     vectorized: bool = True,
# ) -> np.ndarray:
#     """
#     computes the mean of resampled data
#     """
#     # manipulate the shape
#
#     data = np.swapaxes(data, 0, axis)
#
#     dataShape = data.shape  # keep the original data shape
#     nsample = dataShape[0]
#     indices = np.random.randint(0, nsample, (nboot, nsample))
#
#     if vectorized:
#         dataOut = np.nanmean(data[indices, :], axis=1)
#     else:
#         dataOut = np.nan * np.ones((nboot, *dataShape[1:]))
#         for j in range(nboot):
#             index = indices[j]
#             dataOut[j, :] = np.nanmean(data[index, :], axis=0)
#
#     dataOut = np.reshape(dataOut, (nboot, *dataShape[1:]))
#     dataOut = np.swapaxes(dataOut, 0, axis)
#
#     return dataOut
#
#
if __name__ == "__main__":
    ...
