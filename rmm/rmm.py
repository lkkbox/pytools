from .. import nctools as nct
import numpy as np

# read in the static data for calculating the pcs
var_names: list[str] = ['olr', 'u200', 'u850']
static_data_path: str = '/nwpr/gfs/com120/tools/pytools/rmm/static_rmm.nc'
statics: dict[str: dict[str: np.ndarray]] = {
    vn: {
        'eof': nct.read(static_data_path, f'eof_{vn}'),
        'mean': nct.read(static_data_path, f'mean_{vn}'),
        'variance': nct.ncreadatt(static_data_path, '/', f'var_{vn}'),
    }
    for vn in var_names
}
statics['std_pc1'] = nct.ncreadatt(static_data_path, '/', f'std_pc1')
statics['std_pc2'] = nct.ncreadatt(static_data_path, '/', f'std_pc2')


def cal_pc(
    olr:np.ndarray, 
    u200:np.ndarray,
    u850:np.ndarray, 
    sub120:bool=True
) -> tuple[np.ndarray, np.ndarray]:

    data = {'olr': olr, 'u200': u200, 'u850': u850}

    # normalize the data
    for vn in var_names:
        data[vn] = (data[vn] - statics[vn]['mean']) / np.sqrt(statics[vn]['variance'])

    if sub120:
        data = _remove_previous_120(data)

    # projection along the longitude
    pc1 = [
        np.nansum(data[vn] * statics[vn]['eof'][0, :], axis=-1)
        for vn in var_names
    ]

    pc2 = [
        np.nansum(data[vn] * statics[vn]['eof'][1, :], axis=-1)
        for vn in var_names
    ]

    # sum over the three variables and divide by the std(pc)
    pc1 = np.nansum(pc1, axis=0) / statics['std_pc1']
    pc2 = np.nansum(pc2, axis=0) / statics['std_pc2']

    return pc1, pc2


def _remove_previous_120(data:dict[str:np.ndarray]) -> dict[str:np.ndarray]:
    def remove_runmean(y0:np.ndarray):
        nt = y0.shape[0]
        y1 = np.nan * np.ones(y0.shape)

        for it in range(nt):
            if it < 120:
                ts = 0
            else:
                ts = it - 120

            y1[it, :] = y0[it, :] - np.nanmean(y0[ts:it, :], axis=0)

        return y1

    return {
        vn: remove_runmean(data[vn])
        for vn in var_names
    }

    
            
