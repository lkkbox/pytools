#!/nwpr/gfs/com120/.conda/envs/rd/bin/python
from .setup import setModel, multiLevelGrb2Key


def setting():
    # source file name =   DIRROOT + srcMemberDir + srcFileNames

    # =========================================================================================================
    # name             : string: model name
    # dataStructure    : string: structure of output data ('fakeDmsKey', 'mergedGrib2')
    # srcMemberDir     : lambda(year2d, month, day, hour, member) -> str: subdirectory of each member
    # initHours        : integer as list[ hours ]: hours in a day of initiation
    # numMembers       : integer as list[ hours ]: numbers of members of each init hour
    # leadMaxs         : integer as list[ hours ][ members ]: maximum lead time of each member at each init hour
    # srcFileNames
    # => for fakeDmsKey: dict[ variables:list[string], prefix:lambda( year2d, month, day, hour, member, lead)] -> str
    #                    They are filenames for each variable.
    # => for mergedGrib2: lambda( year2d, month, day, hour, member, lead) -> str
    #                    They are filename for each forecast lead.
    # [grib2Keys]      : dict[ variables:lambda(lead)]: They are the entries for "wgrib2 -match 'KEY'"
    # cdoVarName       : dict[ variables:string ]: the variable names in netCDF produced by CDO
    # multiplyConstant : dict[ variables:float ]: the numbers to multiply to the variables for converting units
    # hourShift        : dict[ variables:integer ]: the numbers of hours to add to the time axis in source file
    # leadList         : dict[ variables:list[int]]: the hours of forecast lead of each variable
    # =========================================================================================================    modelName = 'NCEP_CTRL'

    # subdir/file format = 2024/12/0700z/gec00.pgrb2a.0p50.f840.24120700

    modelName = 'NCEP_CTRL'
    return {
        **setModel(
            name=f'{modelName}',
            dataStructure='mergedGrib2',
            srcMemberDir=lambda year2d, month, day, hour, member:
                f'op/{modelName}/20{year2d:02d}/' +
                f'{month:02d}/{day:02d}{hour:02d}z/',
            initHours=[0, 12],
            numMembers=[1, 1],
            leadMaxs=[[840], [384]],
            srcFileNames=lambda year2d, month, day, hour, member, lead:
                f'gec00.pgrb2a.0p50.f{lead:03d}.{year2d:02d}{
                    month:02d}{day:02d}{hour:02d}',
            grib2Keys={
                'u': lambda lead: multiLevelGrb2Key('UGRD'),
                'v': lambda lead: multiLevelGrb2Key('VGRD'),
                't': lambda lead: multiLevelGrb2Key('TMP'),
                'q': lambda lead: multiLevelGrb2Key('SPFH'),
                'z': lambda lead: multiLevelGrb2Key('HGT'),
                'u10': lambda lead: ':UGRD:10 m above ground:',
                'v10': lambda lead: ':VGRD:10 m above ground:',
                't2m': lambda lead: 'TMP:2 m above ground',
                'prec': lambda lead: f':APCP:0 m above ground:{lead-12}-{lead} hour acc fcst:',
                'mslp': lambda lead: 'PRMSL',
                'olr': lambda lead: f':NLWRF:top of atmosphere:{lead} hour fcst:',
            },
            cdoVarName={
                'u': 'u',
                'v': 'v',
                't': 't',
                'q': 'q',
                'z': 'gh',
                'u10': '10u',
                'v10': '10v',
                't2m': '2t',
                'prec': 'param8.1.0',
                'mslp': 'prmsl',
                'olr': 'tnlwrf',
            },
            multiplyConstant={
                'u': 1,
                'v': 1,
                't': 1,
                'q': 1,
                'z': 1,
                'u10': 1,
                'v10': 1,
                't2m': 1,
                'prec': 2,
                'mslp': 1,
                'olr': 1,
            },
            hourShift={
                'u': 0,
                'v': 0,
                't': 0,
                'q': 0,
                'z': 0,
                'u10': 0,
                'v10': 0,
                't2m': 0,
                'prec': -6,
                'mslp': 0,
                'olr': 0,
            },
            leadList={
                'u': [*list(range(6, 384+1, 6)), *list(range(396, 1080+1, 12))],
                'v': [*list(range(6, 384+1, 6)), *list(range(396, 1080+1, 12))],
                't': [*list(range(6, 384+1, 6)), *list(range(396, 1080+1, 12))],
                'q': [*list(range(6, 384+1, 6)), *list(range(396, 1080+1, 12))],
                'z': [*list(range(6, 384+1, 6)), *list(range(396, 1080+1, 12))],
                'u10': list(range(6, 1080+1, 6)),
                'v10': list(range(6, 1080+1, 6)),
                't2m': list(range(6, 1080+1, 6)),
                'prec': list(range(12, 1080+1, 12)),
                'mslp': list(range(6, 1080+1, 6)),
                'olr': [*list(range(6, 384+1, 6)), *list(range(396, 1080+1, 12))],
            }
        )}
