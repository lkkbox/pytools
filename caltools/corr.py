import numpy as np 
'''
module for common correlation calculations
'''


def corrcoef(a:np.ndarray, b:np.ndarray, axis:int) -> np.ndarray:
    '''
    calculate the correlation coefficients of a, b along axis
    return = cov(a, b) / sqrt(cov(a, a) * cov(b, b))
    '''
    return (
        np.nansum(a * b, axis=axis)
        / np.sqrt(
            np.nansum(a ** 2, axis=axis)
            * np.nansum(b ** 2, axis=axis)
        )
    )
