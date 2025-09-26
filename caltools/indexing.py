import numpy as np


def indices(list_in: list, elements: list, allow_missing: bool=False) -> list[int]:
    '''return the indices of elements in the list'''
    if not allow_missing:
        return [list_in.index(e) for e in elements]
    else:
        return [list_in.index(e) for e in elements if e in list_in]


def shared_element_indices(list_1: list, list_2: list) -> tuple[list[int], list[int]]:
    '''return the indices of the elements shared in the both lists'''
    allow_missing = True
    return indices(list_1, list_2, allow_missing), indices(list_2, list_1, allow_missing)


def request_elements(
    data_from: np.ndarray,
    elements_from: list,
    elements_to: list,
    axis: int=0,
    allow_missing: bool=False,
) -> np.ndarray:
    '''return a array by selecting the elements from a list, along an axis'''
    data_from = np.swapaxes(data_from, 0, axis)
    
    # expand/reduce the dimension of axis to list_to
    shape_to = (len(elements_to), *data_from.shape[1:]) 
    data_to = np.nan * np.ones(shape_to)

    inds_from = indices(elements_from, elements_to, allow_missing=allow_missing)
    inds_to = indices(elements_to, elements_from, allow_missing=allow_missing)
    data_to[inds_to, :] = data_from[inds_from, :]

    data_to = np.swapaxes(data_to, 0, axis)
    return data_to
