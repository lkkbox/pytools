#!/nwpr/gfs/com120/.conda/envs/rd/bin/python

def getLevels(): return [10, 30, 50, 100, 200, 300, 500, 700, 850, 925, 1000]

def getVarSettings():
  levels = getLevels()
  var3d = {
    'levelType' : 'pressure', 
    'levels'    : levels,
    }
  var2d = {
    'levelType' : 'surface',
    'levels'    : 'surface',
    }
  varSettings = {
    'u10':  { **var2d},
    'v10':  { **var2d},
    't2m':  { **var2d},
    'mslp': { **var2d},
    'olr':  { **var2d},
    'prec': { **var2d},
    'u':    { **var3d},
    'v':    { **var3d},
    't':    { **var3d},
    'q':    { **var3d},
    'z':    { **var3d},
  }
  return varSettings

def multiLevelDmsKey( subdmskey):
  return [ f'{l:03d}{subdmskey}'  if l < 1000 else f'H00{subdmskey}' for l in getLevels()]

def multiLevelGrb2Key( grib2Key):
  keys = [ f':{grib2Key}:{l} mb:' for l in getLevels()]
  keys = '|'.join(keys)
  return keys

def setModel( name, **inArgs ):
  def checkArgs( key, args, validArgs):
    args, validArgs = set( args ), set( validArgs )
    if args != validArgs:
      tooManyArgs = ', '.join([ arg  for arg in args if arg not in validArgs])
      tooFewArgs  = ', '.join([ arg  for arg in validArgs if arg not in args])
      raise Exception( f'[{key}]: excessive ("{tooManyArgs}") and/or missing ("{tooFewArgs}") arguments')
    return
  def isLambda( o ): return callable( o) and o.__name__ == "<lambda>"
  def getLambdaArgs( o ): return set(o.__code__.co_varnames)
  def typeAndValue( o): return f'{type(o)} : "{o}"'
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
  # =========================================================================================================
  varSettings = getVarSettings()
  TYPE_FAKEDMSKEY = 'fakeDmsKey'
  TYPE_MERGEDGRIB2 = 'mergedGrib2'
  # ----------------------------------------------------------------------------------------------------------------
  if inArgs['dataStructure'] not in [TYPE_FAKEDMSKEY, TYPE_MERGEDGRIB2 ]:
    raise Exception( f'[dataStructure]: must be "fakeDmsKey" or "mergedGrib2, but found "{inArgs['dataStructure']}"')
  # ---- check inputs
  # ----------------------------------------------------------------------------------------------------------------
  validInArgs = [ 'dataStructure','srcMemberDir', 'initHours', 
    'numMembers', 'leadMaxs', 'srcFileNames', 'cdoVarName', 'multiplyConstant', 'hourShift', 'leadList']
  if inArgs['dataStructure'] == TYPE_MERGEDGRIB2:
    validInArgs.append('grib2Keys')
  checkArgs( 'setModel', inArgs.keys(), validInArgs)
  # ----------------------------------------------------------------------------------------------------------------
  arg = inArgs['srcMemberDir']
  if not isLambda( arg ):
    raise Exception( f'[srcMemberDir]: must be of the lambda type, but found {typeAndValue(arg)}')
  if not getLambdaArgs( arg ) == set(['year2d', 'month', 'day', 'hour', 'member']):
    raise Exception( f'[srcMemberDir]: has wrong lambda inputs arguments.')
  arg( year2d=10, month=10, day=10, hour=10, member=10 ) # test run the lambda
  # ----------------------------------------------------------------------------------------------------------------
  arg = inArgs['initHours']
  if not isinstance( arg, list):
    raise Exception( f'[initHours]: must be of the list type, but found {typeAndValue(arg)}')
  for initHour in arg:
    if not isinstance( initHour, int):
      raise Exception( f'[initHours]: each initHour must be an integer, but found "{type(initHour)}')
    if initHour < 0 or initHour >= 24:
      raise Exception( f'[initHours]: each initHour must be >= 0 and < 24 ')
  numInitHours = len( arg)
  # ----------------------------------------------------------------------------------------------------------------
  arg = inArgs['numMembers']
  if not isinstance( arg, list):
    raise Exception( f'[numMembers]: must be of the list type, but found {typeAndValue(arg)}')
  for num in arg:
    if not isinstance( num, int):
      raise Exception( f'[numMembers]: each num must be an integer, but found {typeAndValue(num)}')
    if num < 1:
      raise Exception( f'[numMembers]: each num must be > 0 ')
  if numInitHours != len( arg):
    len1, len2 = numInitHours, len(arg)
    raise Exception(f'[numMembers]: numInitHours (len={len1}) and numMembers (len={len2}) must have the same number of elements to specify for each init.')
  # ----------------------------------------------------------------------------------------------------------------
  arg = inArgs['leadMaxs']
  if not isinstance( arg, list):
    raise Exception( f'[leadMaxs]: must be of the list type, but found {typeAndValue(arg)}')
  if numInitHours != len( arg):
    len1, len2 = numInitHours, len(arg)
    raise Exception(f'[leadMaxs]: numInitHours (len={len1}) and leadMaxs (len={len2}) must have the same number of elements to specify for each init.')
  for leadMax, numMembers in zip( arg, inArgs['numMembers']):
    if not isinstance( leadMax, list):
      raise Exception( f'[leadMaxs]: each element must be of the list type, but found {typeAndValue(leadMax)}')
    if len( leadMax ) != numMembers:
      raise Exception(f'[leadMaxs]: the element (len={len(leadMax)}) and members (n={numMembers}) must be the same to specify for each member.')
    for l in leadMax:
      if not isinstance( l, int):
        raise Exception( f'[leadMaxs]: leadMax[imember] must be an integer, but found {typeAndValue(l)}')
  # ----------------------------------------------------------------------------------------------------------------
  arg = inArgs['srcFileNames']
  if inArgs['dataStructure'] == TYPE_MERGEDGRIB2:
    if not isLambda( arg ):
      raise Exception( f'[srcFileNames]: must be of the lambda type, but found {typeAndValue(value)}')
    if not getLambdaArgs( arg ) == set(['year2d', 'month', 'day', 'hour', 'member', 'lead']):
      raise Exception( f'[srcFileNames]: has wrong lambda inputs arguments.')
    arg( year2d=10, month=10, day=10, hour=10, member=10, lead=6 ) # test run the lambda
  if inArgs['dataStructure'] == TYPE_FAKEDMSKEY:
    if not isinstance( arg, dict):
      raise Exception( f'[srcFileNames]: must be of the dict type, but found {typeAndValue(arg)}')
    checkArgs( 'srcFileName', arg.keys(), ['prefix', *varSettings.keys()])
    for key, value in arg.items():
      if key in varSettings:
        if not isinstance( value, list):
          raise Exception( f'[srcFileNames]: must be of the list type, but found {typeAndValue(value)} for {key}')
        for f in value: 
          if not isinstance( f, str):
            raise Exception( f'[srcFileNames]: elements must be of the string type, but found {typeAndValue(f)} for {key}')
      elif key == 'prefix':
        if not isLambda( value ):
          raise Exception( f'[srcFileNames]: must be of the lambda type, but found {typeAndValue(value)}')
        if not getLambdaArgs( value ) == set(['year2d', 'month', 'day', 'hour', 'member', 'lead']):
          raise Exception( f'[srcFileNames]: has wrong lambda inputs arguments.')
        value( year2d=10, month=10, day=10, hour=10, member=10, lead=6 ) # test run the lambda
  # ----------------------------------------------------------------------------------------------------------------
  if inArgs['dataStructure'] == TYPE_MERGEDGRIB2:
    arg = inArgs['grib2Keys']
    if not isinstance( arg, dict):
      raise Exception( f'[grib2Keys]: must be of the dict type, but found {typeAndValue(arg)}')
    checkArgs( 'srcFileName', arg.keys(), [*varSettings.keys()])
    for key, value in arg.items():
      if not isLambda( value ):
        raise Exception( f'[grib2Keys][{key}]: must be of the lambda type, but found {typeAndValue(value)}')
      if not getLambdaArgs( value ) == set(['lead']):
        raise Exception( f'[grib2Keys][{key}]: has wrong lambda inputs arguments.')
      value( lead=6 ) # test run the lambda
  # ----------------------------------------------------------------------------------------------------------------
  arg = inArgs['cdoVarName']
  if not isinstance( arg, dict):
    raise Exception( f'[cdoVarName]: must be of the dict type, but found {typeAndValue(arg)}')
  checkArgs( 'cdoVarName', arg.keys(), varSettings.keys())
  for key, value in arg.items():
    if not isinstance( value, str):
      raise Exception( f'[cdoVarName]: must be of the string type, but found {typeAndValue(value)} for {key}')
  # ----------------------------------------------------------------------------------------------------------------
  arg = inArgs['multiplyConstant']
  if not isinstance( arg, dict):
    raise Exception( f'[multiplyConstant]: must be of the dict type, but found {typeAndValue(arg)}')
  checkArgs( 'multiplyConstant', arg.keys(), varSettings.keys())
  for key, value in arg.items():
    if not (isinstance( value, int) or isinstance( value, float)):
      raise Exception( f'[multiplyConstant]: must be of the string type, but found {typeAndValue(value)} for {key}')
  # ----------------------------------------------------------------------------------------------------------------
  arg = inArgs['hourShift']
  if not isinstance( arg, dict):
    raise Exception( f'[hourShift]: must be of the dict type, but found {typeAndValue(arg)}')
  checkArgs( 'hourShift', arg.keys(), varSettings.keys())
  for key, value in arg.items():
    if not (isinstance( value, int) or isinstance( value, float)):
      raise Exception( f'[hourShift]: must be of the string type, but found {typeAndValue(value)} for {key}')
  # ----------------------------------------------------------------------------------------------------------------
  arg = inArgs['leadList']
  if not isinstance( arg, dict):
    raise Exception( f'[leadList]: must be of the dict type, but found {typeAndValue(arg)}')
  checkArgs( 'leadList', arg.keys(), varSettings.keys())
  for key, value in arg.items():
    if not isinstance( value, list):
      raise Exception( f'[leadList]: must be of the list type, but found {typeAndValue(value)} for {key}')
    for e in value:
      if not isinstance( e, int) or e < 0:
        raise Exception( f'[leadList]: elements must be integers indicating forecast hours but found {typeAndValue(e)} for {key}')
  # ----------------------------------------------------------------------------------------------------------------
  return {name: inArgs}


def example():
  modelSettings = {
    **setModel(
      name             = 'modelName',
      dataStructure    = 'mergedGrib2',
      srcMemberDir     = lambda year2d, month, day, member, hour: f'{year2d}{month}{day}{hour}{member}',
      initHours        = [0, 12],
      numMembers       = [3, 10],
      leadMaxs         = [[1080 for i in range(3)], [1080 for i in range(10)]],
      srcFileNames     = {
        'prefix': lambda year2d, month, day, hour, member, lead: f'{year2d}',
        'u'   : ['u.nc'],
        'v'   : ['v.nc'],
        't'   : ['t.nc'],
        'q'   : ['q.nc'],
        'z'   : [''],
        'u10' : ['u10.nc'],
        'v10' : ['v10.nc'],
        't2m' : ['t2m.nc'],
        'prec': ['prec.nc'],
        'mslp': ['mslp.nc'],
        'olr' : ['olr.nc'],
        },
      cdoVarName = {
        'u'   :'u.nc',
        'v'   :'v.nc',
        't'   :'t.nc',
        'q'   :'q.nc',
        'z'   :'',
        'u10' :'u10.nc',
        'v10' :'v10.nc',
        't2m' :'t2m.nc',
        'prec':'prec.nc',
        'mslp':'mslp.nc',
        'olr' :'olr.nc',
        },
      multiplyConstant = {
        'u'   : 1,
        'v'   : 1,
        't'   : 1,
        'q'   : 1,
        'z'   : 1,
        'u10' : 1.2,
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
        'prec': 0.1,
        'mslp': 0,
        'olr' : 0,
        },
      leadList = {
        'u'   :[*list(range(6,384+1,6)), *list(range(396, 1080+1, 12))], 
        'v'   :[*list(range(6,384+1,6)), *list(range(396, 1080+1, 12))], 
        't'   :[*list(range(6,384+1,6)), *list(range(396, 1080+1, 12))], 
        'q'   :[*list(range(6,384+1,6)), *list(range(396, 1080+1, 12))], 
        'z'   :[*list(range(6,384+1,6)), *list(range(396, 1080+1, 12))], 
        'u10' :list(range(6,1080+1,6)), 
        'v10' :list(range(6,1080+1,6)), 
        't2m' :list(range(6,1080+1,6)), 
        'prec':list(range(24,1080+1,24)),
        'mslp':list(range(6,1080+1,6)), 
        'olr' :[*list(range(6,96,6)), *list(range(96, 1080+1, 12))],
      }
    ),
    }

  print( modelSettings )

if __name__ == '__main__':
  example()
