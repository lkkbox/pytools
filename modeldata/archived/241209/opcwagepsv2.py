#!/nwpr/gfs/com120/.conda/envs/rd/bin/python 
from .setup import setModel, multiLevelDmsKey
from .get import run
from pytools import timetools as tt


def setting():
  # source file name =   DIRROOT + srcMemberDir + srcFileNames
  # =============================================================================================
  # [MODEL SETTING]
  # name             : string: model name
  # dataStructure    : string: structure of output data ('fakeDmsKey', 'mergedGrib2')
  # srcMemberDir     : lambda(year2d, month, day, hour, member): subdirectory of each member
  # initHours        : integer as list[ hours ]: hours in a day of initiation 
  # numMembers       : integer as list[ hours ]: numbers of members of each init hour
  # leadMaxs         : integer as list[ hours ][ members ]: maximum lead time of each member at each init hour
  # srcFileNames     : dict[ variables:list[string], prefix:lambda( year2d, month, day, hour, member, lead)]: filenames of each variable
  # cdoVarName       : dict[ variables:string ]: the variable names in netCDF produced by CDO
  # multiplyConstant : dict[ variables:float ]: the numbers to multiply to the variables for converting units
  # hourShift        : dict[ variables:integer ]: the numbers of hours to add to the time axis in source file
  # leadList         : dict[ variables:list[int]]: the hours of forecast lead of each variable
  # =============================================================================================
  return {
    **setModel(
      name             = 'CWA_GEPSv2',
      dataStructure    = 'fakeDmsKey',
      srcMemberDir     = lambda year2d, month, day, hour, member: f'op/CWA_GEPSv2/{year2d:02d}{month:02d}{day:02d}{hour:02d}/E{member:03d}/',
      initHours        = [  0  , 12   ],
      numMembers       = [ 32+1, 32+1 ],
      leadMaxs         = [ 
         [ 1080 for m in range(32+1)], # 00z
         [*[ 840 for member in range( 10 + 1)], *[168 for member in range(11, 32 + 1)]] # 12z
        ],
      srcFileNames     = {
        'prefix': lambda year2d, month, day, hour, member, lead: f'20{year2d:02d}{month:02d}{day:02d}{hour:02d}{lead:04d}/',
        'u'   : multiLevelDmsKey('200GI0G'),
        'v'   : multiLevelDmsKey('210GI0G'),
        't'   : multiLevelDmsKey('100GI0G'),
        'q'   : multiLevelDmsKey('500GI0G'),
        'z'   : multiLevelDmsKey('000GI0G'),
        'u10' : ['B10200GI0G'],
        'v10' : ['B10210GI0G'],
        't2m' : ['B02100GI0G'],
        'prec': ['B00623GI0G'],
        'mslp': ['SSL010GI0G'],
        'olr' : ['X00340GI0G'],
        },
      cdoVarName = {
        'u'   : 'u',
        'v'   : 'v',
        't'   : 't',
        'q'   : 'q',
        'z'   : 'gh',
        'u10' : '10u',
        'v10' : '10v',
        't2m' : '2t',
        'prec': 'param8.1.0',
        'mslp': 'prmsl',
        'olr' : 'tnlwrf',
        },
      multiplyConstant = {
        'u'   : 1,
        'v'   : 1,
        't'   : 1,
        'q'   : 1,
        'z'   : 1,
        'u10' : 1,
        'v10' : 1,
        't2m' : 1,
        'prec': 4,
        'mslp': 1,
        'olr' : 1,
        },
      hourShift = {
        'u'   : 0,
        'v'   : 0,
        't'   : 0,
        'q'   : 0,
        'z'   : 0,
        'u10' : 0,
        'v10' : 0,
        't2m' : 0,
        'prec': -3,
        'mslp': 0,
        'olr' : 0,
        },
      leadList = {
        'u'   : [*list(range(6,384+1,6)), *list(range(396, 1080+1, 12))], 
        'v'   : [*list(range(6,384+1,6)), *list(range(396, 1080+1, 12))], 
        't'   : [*list(range(6,384+1,6)), *list(range(396, 1080+1, 12))], 
        'q'   : [*list(range(6,384+1,6)), *list(range(396, 1080+1, 12))], 
        'z'   : [*list(range(6,384+1,6)), *list(range(396, 1080+1, 12))], 
        'u10' : list(range(6,1080+1,6)), 
        'v10' : list(range(6,1080+1,6)), 
        't2m' : list(range(6,1080+1,6)), 
        'prec': list(range(6,1080+1,6)),
        'mslp': list(range(6,1080+1,6)), 
        'olr' : [*list(range(6,96,6)), *list(range(96, 1080+1, 12))],
      }
    ),
    }
