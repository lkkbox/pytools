from ..checktools import checkType
from ..terminaltools import FlushPrinter
import numpy as np
from typing import Callable
'''
module for calculating the statistics by the bootstrapping method
'''


def test():
    from functools import partial
    data = np.random.random((5, 4, 3))
    out = resampled_stat([data], partial(np.nanmean, axis=0), 10)
    print(out.shape)
    print(out)


def resampled_stat(
    datas_in: list[np.ndarray], 
    stat_func: Callable, 
    n_boot: int, 
    unit_shape: tuple[int] | list[int] | None = None,
):
    '''
    repeat calculating the statics using stat_func with bootstrapping datas as input
    '''
    checkType(datas_in, list, 'datas_in')
    checkType(stat_func, Callable, 'stat_func')
    checkType(n_boot, int, 'n_boot')
    checkType(unit_shape, [list, int, None], 'unit_shape')
    for data in datas_in:
        checkType(data, np.ndarray, 'elements in datas_in')

    if unit_shape is not None:
        for e in unit_shape:
            checkType(e, int, 'elements in unit_shape')

    else:
        det_output = stat_func(*datas_in)
        unit_shape = det_output.shape

    # create the empty array
    boot_shape = (n_boot, *unit_shape)
    data_boot = np.nan * np.ones(boot_shape)

    # for each input data
    n_sample = datas_in[0].shape[0]
    indices = np.random.randint(0, n_sample, n_sample * n_boot)
    indices = np.reshape(indices, (n_boot, n_sample))

    fp = FlushPrinter()
    if (datas_in[0].ndim) > 1:
        for i in range(n_boot):
            fp.flush(f' bootstrapping resampling {i}/{n_boot}..')
            datas = [data_in[indices[i, :], :] for data_in in datas_in]
            data_boot[i, :] = stat_func(*datas)
    else:
        for i in range(n_boot):
            fp.flush(f' bootstrapping resampling {i}/{n_boot}..')
            datas = [data_in[indices[i, :]] for data_in in datas_in]
            data_boot[i] = stat_func(*datas)

    return data_boot


def percentile(
    datas_in: list[np.ndarray], 
    stat_func: Callable, 
    n_boot: int, 
    prs: list[int|float],
):
    '''
    calculate the percentiles of resampled stats
    '''
    checkType(datas_in, list, 'datas_in')
    checkType(stat_func, Callable, 'stat_func')
    checkType(n_boot, int, 'n_boot')
    checkType(prs, list, 'prs')
    for data in datas_in:
        checkType(data, np.ndarray, 'elements in datas_in')
    for pr in prs:
        checkType(pr, [list, int], 'elements in prs')

    boots = resampled_stat(datas_in, stat_func, n_boot)
    return np.percentile(boots, prs, axis=0)


def diff_level(
    datas_in1: list[np.ndarray], 
    datas_in2: list[np.ndarray], 
    stat_func: Callable, 
    n_boot: int, 
):
    resampled1 = resampled_stat(datas_in1, stat_func, n_boot)
    resampled2 = resampled_stat(datas_in2, stat_func, n_boot)
    return np.nansum((resampled1 > resampled2), 0) / n_boot


def diff_level_const(
    datas_in: list[np.ndarray], 
    const: float | int, 
    stat_func: Callable, 
    n_boot: int, 
):
    resampled = resampled_stat(datas_in, stat_func, n_boot)
    return np.nansum((resampled > const), 0) / n_boot

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


if __name__ == '__main__':
    test()
