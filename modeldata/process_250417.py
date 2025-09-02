from pytools.plottools import FlushPrinter as Fp
import pytools.timetools as tt
import pytools.nctools as nct
import os
import logging
import subprocess
from collections.abc import Iterable
from math import ceil

# TODO: check if file need update


def plevDmsKeys(key, levelsInHpa):
    return [
        f'{level:03d}{key}' if level != 1000
        else f'H00{key}'
        for level in levelsInHpa
    ]


class Processor:
    # ------------------------------------------ #
    # Go to _runSlice to see the main procedures #
    # ------------------------------------------ #
    def __init__(p, modelName, rootDesDir, rootSrcDir,
                 workDir, gridFile, srcPathLambda, initTimes, members,
                 variables, forceUpdate=False, printDesSummary=False, debug=False):
        p.modelName = modelName
        p.rootDesDir = rootDesDir
        p.rootSrcDir = rootSrcDir
        p.workDir = workDir
        p.gridFile = gridFile
        p.filePath = srcPathLambda
        p.initTimes = initTimes
        p.members = members
        p.variables = variables
        p.forceUpdate = forceUpdate
        p.printDesSummary = printDesSummary
        p.debug = debug
        p._checkConstructor()


        p.fp = Fp()
        p.tempFile = p._getWorkFile('tmp')
        p.logFile = p._getWorkFile('log')
        p.status = True
        p._initLogging()
        p.validOutputTypes = _getValidOutputTypes()

        p.CDO = '/nwpr/gfs/com120/.conda/envs/rd/bin/cdo -P 8 --no_history --reduce_dim'
        p.WGRIB2 = '/usr/bin/wgrib2 -ncpu 1'
        p.NC_COMPRESS = '/nwpr/gfs/com120/0_tools/bashtools/nc_compress'

        logging.info(f'tempFile = {p.tempFile}')
        logging.info(f'logFile  = {p.logFile}')

    def _checkConstructor(p):

        _checkType(p.modelName, str, 'modelName')
        _checkType(p.rootDesDir, str, 'rootDesDir')
        _checkType(p.rootSrcDir, str, 'rootSrcDir')
        _checkType(p.workDir, str, 'workDir')
        _checkType(p.filePath, 'lambda', 'filePath')
        _checkType(p.gridFile, str, 'gridFile')
        _checkType(p.initTimes, list, 'initTimes')
        _checkType(p.members, list, 'members')
        _checkType(p.variables, list, 'variables')
        _checkType(p.forceUpdate, bool, 'forceUpdate')
        _checkType(p.printDesSummary, bool, 'printDesSummary')
        for v in p.variables:
            _checkType(v, Variable, 'variable')

        _checkLambdaArgs(p.filePath,
                         ('initTime', 'member', 'lead', 'fileNameKey'), 'filePath')
        
        if not os.path.exists(p.gridFile):
            raise FileNotFoundError(f'grid file {p.gridFile}')

    def _getWorkFile(p, logOrTemp):
        workFile = p.workDir + '/' + p.modelName + '.' + logOrTemp + \
            '.' + tt.float2format(tt.now(), '%y%m%d_%H%M%S')

        # check permission and file existence
        if not os.access(p.workDir, os.W_OK):
            raise PermissionError(p.workDir)
        if os.path.isfile(workFile) or os.path.islink(workFile):
            raise FileExistsError(workFile)

        return workFile

    def _initLogging(p):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            datefmt='%Y-%m-%d %H:%M',
            handlers=[
                logging.FileHandler(p.logFile),
                logging.StreamHandler()
            ]
        )

    def run(p):  # run all
        for p.initTime in p.initTimes:
            for p.member in p.members:
                for p.variable in p.variables:
                    
                    p.fp.print('---- ---- ----')
                    logging.info(f'[[ model    ]] = {p.modelName}')
                    logging.info(f'[[ initTime ]] = {
                                 tt.float2format(p.initTime, '%Y-%m-%d %Hz')}')
                    logging.info(f'[[ member   ]] = {p.member}')
                    logging.info(f'[[ variable ]] = {p.variable.varName}')
                    p._runSlice()

    def _runSlice(p):
        # 1. setup
        # 2. check need update?
        # 3. merge grib2 files
        # 4. convert to netCDF4

        # for analysis output
        if 'analysis' in p.variable.outputTypes:
            p.outputTypes = ['analysis']
            p.leads = [0]
            p.status = True  # False if error has occured
            p._getSrcPaths()
            p._getDesPaths()
            p._run_createDesDir()
            p._run_checkFileNeedUpdate()
            p._run_mergeGrib2()
            p._run_grib2toNC()

        # for others
        p.outputTypes = [o for o in p.variable.outputTypes if o != 'analysis']
        if p.outputTypes:
            p.leads = p.variable.leads  # all leads
            p.status = True
            p._getSrcPaths()
            p._getDesPaths()
            p._run_createDesDir()
            p._run_checkFileNeedUpdate()
            p._run_mergeGrib2()
            p._run_grib2toNC()

        p.outputTypes = p.variable.outputTypes
        p._getDesPaths()
        p._run_compressNC()
        p._printDesFileSummary()

        if os.path.exists(p.tempFile) and not p.debug:
            os.remove(p.tempFile)  # cleanup

    def _runCommand(p, command, printCommand=False, printResult=False,
                    sendToBackground=False, formatCommand='{}', formatResult='{}'
                    ):
        if not p.status:  # don't do anything if error has occured
            return 1, None

        if printCommand:
            p.fp.print(formatCommand.format(command))
        else:
            p.fp.flushPrint(formatCommand.format(command))

        if sendToBackground:
            subprocess.Popen(
                command.split(), 
                stdout=subprocess.DEVNULL,
            )
            return 0, None

        status, result = subprocess.getstatusoutput(command)

        if printResult:
            p.fp.print(formatResult.format(result))

        if status != 0:
            p.fp.print('')
            logging.info(command)
            logging.error(result)
        return status, result

    def _run_createDesDir(p):
        if not p.status:
            return
        desDir = os.path.dirname(list(p.desPaths.values())[0])
        if not os.path.exists(desDir):
            p._runCommand(f'mkdir -p {desDir}')

    def _run_checkFileNeedUpdate(p):
        # 1. is any file missing?
        # 2. TODO: is any file incomplete?
        if not p.status:
            return

        p._filesNeedUpdate = {key: True for key in p.outputTypes}

        if p.forceUpdate:
            logging.info('[[    Force updating all files.    ]]')
            return

        for p.outputType in p.desPaths:
            desPath = p.desPaths[p.outputType]

            if not os.path.exists(desPath):
                p._filesNeedUpdate[p.outputType] = True
                continue

            summary = p._getDesFileSummary()
            if summary['varName'] is None:
                logging.info(
                    f'updating {p.outputType} because the VARNAME is not found.')
                p._filesNeedUpdate[p.outputType] = True
                continue

            if len(summary['time']) == 0:
                logging.info(
                    f'updating {p.outputType} because "time" is not found.')
                p._filesNeedUpdate[p.outputType] = True
                continue

            time = summary['time']
            if p.leads:
                maxPossibleValidDays = (p.leads[-1]+p.variable.shiftHour) / 24
            else:
                maxPossibleValidDays = p.variable.shiftHour/24

            existingLeadDays = time[-1] - p.initTime

            p.variable._getCdoOperators()
            expectedLeadDays = p.variable.cdoOperators[p.outputType]['maxValidDays']
            if expectedLeadDays == -1:
                # take the maximum possible from the src files
                expectedLeadDays = maxPossibleValidDays
            else:
                expectedLeadDays += p.variable.shiftHour/24

            if expectedLeadDays > maxPossibleValidDays:  
                expectedLeadDays = maxPossibleValidDays

            existingLeadDays = ceil(existingLeadDays)
            expectedLeadDays = ceil(expectedLeadDays)

            if existingLeadDays < expectedLeadDays:
                p._filesNeedUpdate[p.outputType] = True
                logging.info(
                    f'updating {p.outputType} because the file is incomplete: ' +
                    f'(expected, existing) = ({expectedLeadDays}, {existingLeadDays}).'
                )
                continue

            logging.info(
                f'skipping {p.outputType} because the file is completed: ' +
                f'valid = {existingLeadDays}.'
            )
            p._filesNeedUpdate[p.outputType] = False

    def _run_mergeGrib2(p):
        # 1. remove tempFile
        # 2. locate the records to extract from the grib2 file
        # 3. append to the tempFile (merge)
        def getCommandGrib2Match(srcPath):
            command = f'{
                p.WGRIB2} -match "({'|'.join(p.variable.grib2Matches)})"'
            command += f' {srcPath}'
            return command

        def getRecordNumbers(srcPath):
            # use wgrib2 to locate the grib2 keys
            status, output = p._runCommand(getCommandGrib2Match(srcPath))

            if status != 0 or output is None:
                return []  # error output

            lines = output.split('\n')
            records = [r for r in lines if r != '' and r[:8] != 'Warning:']
            # somehow an empty string can be returned from wgrib2..
            # remove the warning as well

            # check if there are duplicate records
            # by removing the wgrib2 record number and byte size -> [2:]
            # (because prec in TGFS 0-6h are duplicated,
            #  and messed up the counting...)
            splittedRecords = [r.split(':')[2:] for r in records]

            iUniqueRecords = [
                i for i, c, in enumerate(splittedRecords)
                if c not in splittedRecords[i+1:]
            ]   # finding the unique record and get the index
            return [
                records[i].split(':')[0] for i in iUniqueRecords
            ]   # get the record number from wgrib2 -> [0]

        def appendRecords(srcPath, recNums):
            command = f'{
                p.WGRIB2} -match "^({'|'.join([f'{n}:' for n in recNums])})"'
            command += f' {srcPath} -append -grib {p.tempFile}'
            p._runCommand(command)

        def reportWrongNumRecords():
            expected = p.variable.numRecordsPerFile
            encountered = len(recNums)
            p.fp.print(getCommandGrib2Match(srcPath))
            logging.warning(
                f'Expecting {expected} records ' +
                f'but found {encountered} in {srcPath}'
            )

        # =================================== #
        if not p.status:
            return

        # do nothing if no files need updated
        if not any([p._filesNeedUpdate[key] for key in p.desPaths]):
            return

        # 1. remove tempFile: clean up the previous step
        if os.path.isfile(p.tempFile):
            os.remove(p.tempFile)

        # 2. locate the records to extract from the grib2 file
        recordNumbers = []
        for srcPath in p.srcPaths:
            recNums = getRecordNumbers(srcPath)
            if p.variable.numRecordsPerFile != len(recNums):
                reportWrongNumRecords()
                break
            recordNumbers.append(recNums)

        if len(recordNumbers) == 0:
            p.status = False
            logging.error('no records are retreived.')

        # 3. append to the tempFile (merge)
        for srcPath, recNums in zip(p.srcPaths, recordNumbers):
            appendRecords(srcPath, recNums)

    def _run_grib2toNC(p):
        def getCdoCommand(operator, desPath):
            operatorStr = operator2string(operator)

            command = f'{p.CDO} -f nc4 {operatorStr} -setgrid,{p.gridFile}'
            command += f' {p.tempFile} {desPath}'
            return command

        def operator2string(operator):
            prefix = operator['prefix']
            suffix = operator['suffix']
            if isinstance(operator['body'], str):
                body = operator['body']
            elif _isLambda(operator['body']):
                body = operator['body'](p.initTime)
            else:
                raise ValueError(f'unrecognize {operator['body']=}')
            return prefix + body + suffix
        
        for outputType in p.outputTypes:
            if not p.status:
                return
            
            if not p._filesNeedUpdate[outputType]:
                continue

            p.variable._getCdoOperators()
            operator = p.variable.cdoOperators[outputType]
            command = getCdoCommand(operator, p.desPaths[outputType])
            status, __ = p._runCommand(command)
            if status == 0:
                p.fp.flushPrint('')
                logging.info(f'ok: {outputType}')

    def _run_compressNC(p):
        def getCommand(desPath):
            return f'{p.NC_COMPRESS} {desPath} -1'
        if not p.status:
            return
        for __, desPath in p.desPaths.items():
            if os.path.exists(desPath):
                p._runCommand(getCommand(desPath), sendToBackground=True)

    def _getDesFileSummary(p):
        desPath = p.desPaths[p.outputType]
        summary = {
            'desPath': desPath[(len(p.rootDesDir)+1+len(p.modelName)+1):],
            'fileExists': None,
            'varNames': [],
            'dimNames': [],
            'varShapes': [],
            'varName': None,
            'varShape': None,
            'dimName': None,
            'time': [],
        }

        # check file exists
        if not os.path.exists(desPath):
            summary['fileExists'] = False
            return summary

        summary['fileExists'] = True

        # check variable names
        varNames = nct.getVarNames(desPath)
        if p.variable.varName not in varNames:
            varShapes = [nct.getVarShape(desPath, vn) for vn in varNames]
            for varName, varShape in zip(varNames, varShapes):
                if len(varShape) == 1:
                    continue
                dimNames = nct.getDimNames(desPath, varName)
                summary['varNames'].append(varName)
                summary['dimNames'].append(dimNames)
                summary['varShapes'].append(varShape)
            return summary

        varName = p.variable.varName
        summary['varName'] = p.variable.varName
        summary['varShape'] = nct.getVarShape(desPath, varName)
        summary['dimName'] = nct.getDimNames(desPath, varName)

        if 'time' not in varNames and p.outputType != 'analysis':
            return summary

        if p.outputType == 'analysis':
            summary['time'] = [p.initTime] # analysis file doesn't have time dimension
        else:
            summary['time'] = nct.ncreadtime(desPath)

        return summary

    def _printDesFileSummary(p):
        if not p.printDesSummary or not p.status:
            return

        for p.outputType in p.outputTypes:
            summary = p._getDesFileSummary()

            # check file exists
            if not summary['fileExists']:
                p.fp.print(f'failed, file not found {summary['desPath']}')
                continue
            p.fp.print(f'[output file summary] {summary['desPath']}')

            # show variable names
            if summary['varName'] is None:
                p.fp.print(f'Error: output does not have the variable "{
                           p.variable.varName}"')
                for varName, varShape, dimName in zip(
                    summary['varNames'],
                    summary['varShapes'],
                    summary['dimNames'],
                ):
                    p.fp.print(f'  {varName} ({','.join(dimName)}) {varShape}')
                continue

            varName = summary['varName']
            varShape = summary['varShape']
            dimName = summary['dimName']
            p.fp.print(f'  {varName} ({','.join(dimName)}) {varShape}')

            time = summary['time']
            if time is None:
                p.fp.print('error: unable to decode time')
                continue

            if len(time) <= 3:
                timeString = (
                    f'{', '.join([
                        tt.float2format(t, '%Y-%m-%d %H:%M:%S')
                        for t in time
                    ])}'
                )
            else:
                timeString = (
                    f'{', '.join([
                        tt.float2format(time[ind], '%Y-%m-%d %H:%M:%S')
                        for ind in [0, 1, 2]
                    ])} ... {tt.float2format(time[-1], '%Y-%m-%d %H:%M:%S')}'
                )
            p.fp.print(f'  Time = {timeString}')

        return

    def _getSrcPaths(p):
        def getSrcPath(lead, fileNameKey):
            return p.rootSrcDir + '/' + p.modelName + '/' + \
                p.filePath(p.initTime, p.member, lead, fileNameKey)
        
        srcPaths, leads = [], []
        stopLoop = False
        for lead in p.leads:
            for fileNameKey in p.variable.fileNameKeys:
                srcPath = getSrcPath(lead, fileNameKey)
                if not os.path.exists(srcPath):
                    logging.warning(f'src file path not found: {lead=} {fileNameKey=}')
                    logging.warning(f'{srcPath}')
                    stopLoop=True
                    break
                srcPaths.append(srcPath)
                # couting the existing leads by srcfiles 
                # to determine if updating the output makes sense
                if lead not in leads:
                    leads.append(lead)

            if stopLoop:
                break
        
        p.leads = leads
        p.srcPaths = srcPaths

    def _getDesPaths(p):
        p.desPaths = {
            outputType:
                p.rootDesDir + '/' + p.modelName + '/' +
                tt.float2format(p.initTime, '%Y/%m/%dz%H/') +
                f'E{p.member:03d}/' +
                p.variable.fileNames[outputType]
            for outputType in p.outputTypes
        }



class Variable:
    def __init__(v, varName, leads, outputTypes, grib2Matches, numRecordsPerFile=1,
                 cdoVarName='', shiftHour=0, multiplyConstant=1, addConstant=0, fileNameKeys=['']):

        v.varName = varName
        v.fileNameKeys = fileNameKeys
        v.leads = leads
        v.outputTypes = outputTypes
        v.grib2Matches = grib2Matches
        v.numRecordsPerFile = numRecordsPerFile
        v.cdoVarName = cdoVarName
        v.shiftHour = shiftHour
        v.multiplyConstant = multiplyConstant
        v.addConstant = addConstant
        v._checkConstructor()

        v.fileNames = {
            outputType: f'{outputType}_{varName}.nc'
            for outputType in outputTypes
        }

    def _checkConstructor(v):
        _checkType(v.varName, str, 'varName')
        _checkType(v.fileNameKeys, list, 'fileNameKeys')
        _checkType(v.leads, list, 'leads')
        _checkType(v.outputTypes, list, 'outputTypes')
        _checkType(v.grib2Matches, list, 'grib2Matches')
        _checkType(v.numRecordsPerFile, int, 'numRecordsPerFile')
        _checkType(v.cdoVarName, [str], 'cdoVarName')
        _checkType(v.shiftHour, [float, int], 'shiftHour')
        _checkType(v.multiplyConstant, [float, int], 'multiplyConstant')
        _checkType(v.addConstant, [float, int], 'addConstant')

        for e in v.fileNameKeys:
            _checkType(e, str, 'element in fileNameKeys')
        for e in v.leads:
            _checkType(e, int, 'element in leads')
        for e in v.outputTypes:
            _checkType(e, str, 'element in outputTypes')
        for e in v.grib2Matches:
            _checkType(e, str, 'element in grib2Matches')

        validOutputTypes = _getValidOutputTypes()
        invalidOutputTypes = [
            o for o in v.outputTypes
            if o not in validOutputTypes
        ]
        if invalidOutputTypes:
            raise ValueError(f'{invalidOutputTypes=}')

    def _getCdoOperators(v):
        operators = _cdoOperator
        for outputType in operators:
            prefix = ''
            suffix = ''

            if v.shiftHour != 0:
                suffix += f' -shifttime,{v.shiftHour}hours'
            if v.cdoVarName != '':
                prefix += f'-chname,{v.cdoVarName},{v.varName} '
            if v.multiplyConstant != 1:
                prefix += f'-mulc,{v.multiplyConstant} '
            if v.addConstant != 0:
                prefix += f'-addc,{v.addConstant} '

            operators[outputType]['prefix'] = prefix
            operators[outputType]['suffix'] = suffix
        
        v.cdoOperators = operators


def _getValidOutputTypes():
    return list(_cdoOperator.keys())


def _checkType(target, validTypes, codeName):
    # make it iterable for an easier life
    if not isinstance(validTypes, Iterable)\
            or isinstance(validTypes, str):
        validTypes = [validTypes]

    # check None type
    if None in validTypes and target is None:
        return
    elif None in validTypes:
        validTypes.pop(validTypes.index(None))

    # check lambda type
    if 'lambda' in validTypes and _isLambda(target):
        return
    elif 'lambda' in validTypes:
        validTypes.pop(validTypes.index('lambda'))

    # check general types
    if isinstance(target, tuple(validTypes)):
        return

    raise TypeError(  # failed
        f'{codeName} shout be type {
            validTypes}, (found={target}, {type(target)})'
    )


def _checkLambdaArgs(lambdaObj, validArgs, codeName=None, throwError=True):
    args = lambdaObj.__code__.co_varnames
    if args == tuple(validArgs):
        return True  # pass
    elif not throwError:
        return False
    else:
        raise ValueError(
            f'Lambda arguments for "{codeName}" shout be {
                validArgs}, (found={args})'
        )


def _isLambda(target): return callable(
    target) and target.__name__ == '<lambda>'


def _checkCDOoperator(getFunc):
    operators = getFunc()
    for key in operators:
        operator = operators[key]['body']
        maxValidDays = operators[key]['maxValidDays']
        codeName = f'cdo operator for {key}'
        _checkType(operator, [str, 'lambda'], codeName)
        _checkType(maxValidDays, int, maxValidDays)
        if _isLambda(operator):
            _checkLambdaArgs(operator, ['initTime'], f'{codeName}.' +
                             'If you are sure you want to modify the lambda parameters, ' +
                             'make sure to modify "operator2string" in "Processor" before ' +
                             'you suppress the error message here.')
    return operators


@_checkCDOoperator
def _cdoOperator():
    return {
        'analysis': {
            'body': '',
            'maxValidDays': 0,  # 0 from init time
        },
        'global_daily_1p0': {
            'body': '-remapbil,r360x181 -daymean',
            'maxValidDays': -1,  # -1 for maximum possible leads
        },
        'WNP_highFreq_0p25': {
            'body': lambda initTime:
                '-sellonlatbox,90,180,0,55 -remapbil,r1440x720 -seldate,'
                + f'{tt.float2format(initTime, '%Y-%m-%d')},'
                + f'{tt.float2format(initTime+9, '%Y-%m-%d')}',
            'maxValidDays': 9,
        },
        'WNP_highFreq_0p25_long': {
            'body': lambda initTime:
                '-sellonlatbox,90,180,0,55 -remapbil,r1440x720 -seldate,'
                + f'{tt.float2format(initTime, '%Y-%m-%d')},'
                + f'{tt.float2format(initTime+31, '%Y-%m-%d')}',
            'maxValidDays': 31,
        },
        'tropIoPac_qbudget':  {
            'body': '-sellonlatbox,30,210,-15,15 -remapbil,r1440x720',
            'maxValidDays': 45,
        },
    }
