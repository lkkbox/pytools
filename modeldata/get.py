'''
2024/12/05 lkkbox

source file name =   DIRROOT + srcMemberDir + srcFileNames
DESDIR  = DIRROOT + 'processed/{modelName}/20{year2d:02d}/{month:02d}/{day:02d}z{hour:02d}/E{member:03d}/'

DIRROOT/griddes/
DIRROOT/processed/

'''
from .. import timetools as tt
from ..plottools import FlushPrinter as Fp
from ..nctools import getVarDimLength as getNcVarDimLength
import os
import subprocess
import inspect
import logging


def run(
    MODELSETTINGS,
    INITMINMAX,
    DIRROOT,
    MIDFILE,
    DEBUG,
    FORCEUPDATE,
    DRYRUN,
    SKIP_MODEL=[],
    SKIP_INIT=[],
    SKIP_MONTH=[],
    SKIP_MEMBER=[],
    SKIP_VARNAME=[],
    LOGFILE='',
    reverseInit=True,
):

    def getOneModel(modelName):
        def getSrcFiles():
            if modelSetting['dataStructure'] == 'fakeDmsKey':
                srcFiles = getSrcFiles_fakeDmsKey()
            if modelSetting['dataStructure'] == 'mergedGrib2':
                srcFiles = getSrcFiles_mergedGrib2()
            return srcFiles

        def getSrcFiles_fakeDmsKey():
            leadList = modelSetting['leadList'][varName]
            srcFileNames = modelSetting['srcFileNames'][varName]
            srcFiles = []

            for lead in leadList:
                if lead > leadMax:
                    break

                prefix = modelSetting['srcFileNames']['prefix'](
                    year2d=year % 100, month=month, day=day, hour=hour, member=member, lead=lead
                )
                for srcFileName in srcFileNames:
                    srcFile = srcDir + prefix + srcFileName

                    if DEBUG:
                        logging.debug(f'trying to locate {srcFile}')

                    if os.path.isfile(srcFile):
                        srcFiles.append(srcFile)
                    else:
                        logging.warning(f'warning: unable to locate {srcFile}')
                        return srcFiles

            return srcFiles

        def getSrcFiles_mergedGrib2():
            leadList = modelSetting['leadList'][varName]
            srcFileNames = modelSetting['srcFileNames']
            srcFiles = []

            for lead in leadList:
                if lead > leadMax:
                    break

                srcFile = srcDir + srcFileNames(
                    year2d=year % 100, month=month, day=day, hour=hour, member=member, lead=lead
                )
                if DEBUG:
                    logging.debug(f'trying to locate {srcFile}')

                if os.path.isfile(srcFile):
                    srcFiles.append(srcFile)
                else:
                    logging.info(f'warning: unable to locate {srcFile}')
                    return srcFiles
            return srcFiles

        def getDesDir():
            desDir = DIRROOT + \
                'processed/{modelName}/20{year2d:02d}/{month:02d}/{day:02d}z{hour:02d}/E{member:03d}/'
            return desDir.format(modelName=modelName, year2d=year % 100, month=month, day=day, hour=hour, member=member)

        def getDesFile_global():
            return getDesDir() + 'global_1p0_' + varName + '.nc'

        def getDesFile_WNP():
            return getDesDir() + 'wnp_0p25_' + varName + '.nc'

        def mergeFilesToNC(srcFiles):
            cdo = '/nwpr/gfs/com120/.conda/envs/rd/bin/cdo -f nc4 -z zip9 -P 16 -L --reduce_dim'
            cat = '/usr/bin/cat'
            wgrib2 = '/usr/bin/wgrib2 -ncpu 1'

            if modelSetting['levels'][varName] is None:
                numRecords = 1
                doWNP = True
            else:
                numRecords = len(modelSetting['levels'][varName])
                doWNP = False

            griddes = getGridDes(modelName)
            desDir = getDesDir()

            desFile_global = getDesFile_global()
            desFile_WNP = getDesFile_WNP()


            # source grib2 files -> 1 merged grib file
            numSrcFiles = len(srcFiles)

            if os.path.isfile(MIDFILE):
                rmMidFile()
            logging.info(f' catting {numSrcFiles} into 1 file')

            fp = Fp()
            for iFile, srcFile in enumerate(srcFiles):
                fp.flushPrint(f'  {iFile + 1} / {numSrcFiles}..')

                if modelSetting['dataStructure'] == 'fakeDmsKey':
                    cmd = f'{cat} {srcFile} >> {MIDFILE}'  # extract here
                    runCommand(cmd, print_command=DEBUG)

                if modelSetting['dataStructure'] == 'mergedGrib2':
                    lead = modelSetting['leadList'][varName][iFile]

                    # checking the number of records retreived by wgrib2 matching the number of levels
                    cmd_getRecords = f'{wgrib2} {
                        srcFile} -match "({modelSetting['grib2Keys'][varName](lead)})"'
                    result = runCommand(
                        cmd_getRecords, 
                        print_command=False, 
                        forced_run=True
                    )
                    
                    # evaluating the number of records retrieved
                    if result is None:  # no output by wgrib2
                        numUniqueRecords = 0
                    else:
                        lines = result.split('\n')
                        records = [r for r in lines if r != ''] # somehow an empty string can be returned from wgrib2..

                        # remove the wgrib2 line number
                        # and check if there are duplicated records
                        # (because prec in TGFS 0-6h are duplicated, and 
                        #  messed up the counting...)
                        splittedRecords = [r.split(':')[2:] for r in records]
                        iUniqueRecords = [i for i, c, in enumerate(splittedRecords) if c not in splittedRecords[i+1:]]
                        recordPositions = [records[i].split(':')[0] for i in iUniqueRecords]
                        numUniqueRecords = len(recordPositions)


                    # quit looping if the record number is wrong
                    if numUniqueRecords == 0:
                        logging.error('\nFAIL: received 0 records:\n'
                                        + f'command = {cmd_getRecords}\n'
                                        + 'records = None')
                        break
                    elif numUniqueRecords != numRecords:
                        uniqueRecords = [records[i] for i in iUniqueRecords]
                        logging.error(f'\nFAIL: received {numUniqueRecords} records'
                                        + f'( expecting {numRecords})\n'
                                        + f'command = {cmd_getRecords}\n'
                                        + f'records=\n    {'\n    '.join(uniqueRecords)}')
                        break

                    # The record check is passed. Now extract the record and append to MIDFILE
                                                        # -match "^(20|30):" ## for 20, 30 = record pos
                    cmd_getRecords = f'{wgrib2} {srcFile} -match "^({'|'.join(recordPositions)}):"'
                    cmd = f'{cmd_getRecords} -append -grib {MIDFILE}'
                    runCommand(cmd, print_command=DEBUG)

                if iFile+1 == numSrcFiles:
                    print('', end='\n', flush=True)
                    logging.info(' catting files done!')

            if not os.path.isfile(MIDFILE):
                logging.error(
                    f'FAIL: no merged grib2 file')
                return
            elif os.path.getsize(MIDFILE) == 0:
                logging.error(
                    f'FAIL: the merged grib2 file is empty')
                return          

            # create destination folder
            if not os.path.isdir(desDir):
                runCommand(f'mkdir -p {desDir}')


            # 1 merged grib file -> nc file
            # cdo options
            cdoVarName = modelSetting['cdoVarName'][varName]
            hourShift = modelSetting['hourShift'][varName]
            multiplyConstant = modelSetting['multiplyConstant'][varName]
            startDate = init + (modelSetting['leadList'][varName][0] + hourShift)/24

            setTimeAxis = f'-settaxis,{tt.float2format(startDate, '%Y-%m-%d')},12:00:00,1day'
            changeName = f'-chname,{cdoVarName},{varName}'
            shiftTime = f'-shifttime,{hourShift}hours'
            multiplyC = f'-mulc,{multiplyConstant}'

            if cdoVarName == varName:
                changeName = ''
            if hourShift == 0:
                shiftTime = ''
            if multiplyConstant == 1:
                multiplyC = ''
            setWorkers = ''  # cdo behaves buggy if on..

            preSelectRegion = f'{setWorkers} {setTimeAxis} {
                changeName} {multiplyC} -daymean {shiftTime}'
            postSelectRegion = f'-setgrid,{griddes}'

            # global: cdo remap, daymean
            cmd = cdo
            cmd += f' {preSelectRegion}'
            cmd += f' -remapbil,r360x180'
            cmd += f' {postSelectRegion}'
            cmd += f' {MIDFILE} {desFile_global}'
            runCommand(cmd)
            logging.info(f'file done: {desFile_global}')

            # WNP: cdo remap, daymean
            if doWNP:
                cmd = cdo
                cmd += f' {preSelectRegion}'
                cmd += f' -sellonlatbox,100,180,0,40'
                cmd += f' -remapbil,r1440x720'
                cmd += f' {postSelectRegion}'
                cmd += f' {MIDFILE} {desFile_WNP}'
                runCommand(cmd)
                logging.info(f'file done: {desFile_WNP}')

            if not DEBUG:
                rmMidFile()

            return

        def checkDesFileCompleteness():
            # Let's check...
            # If the file is already processed, and the output
            # number of days is correct, then we can skip it.
            #
            # The byproduct is the list of srcFiles, and will 
            # be returned for later use as well.
            desFile_global = getDesFile_global()
            desFile_WNP = getDesFile_WNP()
            existingNT_global = getNcVarDimLength(getDesFile_global(), varName, 0)
            existingNT_WNP = getNcVarDimLength(getDesFile_WNP(), varName, 0)
            doWNP = modelSetting['levels'][varName] is None
            hourShift = modelSetting['hourShift'][varName]

            validTime = [init + l/24 + hourShift/24 for l in modelSetting['leadList'][varName] if l <= leadMax]
            numDays = len(set([int(v) for v in validTime]))

            # global only
            if existingNT_global == numDays and (not doWNP):
                logging.info(
                    f' Skipping completed: (desFile, numDays) = ({desFile_global} , {numDays})')
                isCompleted = True
                return isCompleted, None # return None for source files

            # global and WNP
            if existingNT_global == numDays and existingNT_WNP == numDays:
                logging.info('Skipping completed:'
                            + f'({desFile_global} and {desFile_WNP}'
                            + f' with {numDays = })'
                )
                isCompleted = True
                return isCompleted, None # return None for source files


            # Is the file incomplete because the source files
            # are missing? If so, we consider the file is complete
            # and skip processing.
            #
            # update the valid time by leads from existing source files
            srcFiles = getSrcFiles()
            numSrcFiles = len(srcFiles)
            if modelSetting['levels'][varName] is None:
                numLeads = numSrcFiles
            elif modelSetting['dataStructure'] == 'mergedGrib2':
                numLeads = numSrcFiles
            elif modelSetting['dataStructure'] == 'fakeDmsKey':
                numLeads = int(numSrcFiles/len(modelSetting['levels'][varName]))
            # print(len(modelSetting['leadList'][varName]))
            # print(numLeads)
            validTime = [init + hourShift/24 + modelSetting['leadList'][varName][iLead]/24
                         for iLead in range(numLeads)]
            numDays = len(set([int(v) for v in validTime]))
            # global only
            if existingNT_global == numDays and (not doWNP):
                logging.info(
                    f' Skipping completed: (desFile, numDaysInSrcFiles) = ({desFile_global} , {numDays})')
                isCompleted = True
                return isCompleted, None # return None for source files

            # global and WNP
            if existingNT_global == numDays and existingNT_WNP == numDays:
                logging.info('Skipping completed:'
                            + f'({desFile_global} and {desFile_WNP}'
                            + f' with numDaysInSrcFiles = {numDays})'
                )
                isCompleted = True
                return isCompleted, None # return None for source files
            
            # I'm sure the file is incomplete now.
            # Let's go back and process from the source files.
            # Also, tell me why we are processing the existing output file
            if os.path.isfile(desFile_global) or os.path.islink(desFile_global):
                logging.info(f'file incomplete (file, days expected, days in file):'
                             + f'({desFile_global}, {numDays}, {existingNT_global})')
            if os.path.isfile(desFile_WNP) or os.path.islink(desFile_WNP):
                logging.info(f'file incomplete (file, days expected, days in file):'
                             + f'({desFile_WNP}, {numDays}, {existingNT_WNP})')
            
            isCompleted = False
            return isCompleted, srcFiles
            
        # ======================================================
        # ======================================================
        # ======================================================
        modelSetting = MODELSETTINGS[modelName]
        # get data from initMin to initMax
        initMin = INITMINMAX[0]
        initMax = INITMINMAX[1]

        # find 00z and 00z in between
        initHours = modelSetting['initHours']
        initList = [
            d + h/24 for h in initHours for d in range(int(initMin), int(initMax)+1)]
        if reverseInit:
            initList = initList[::-1]
        logging.info(f' len( initList ) = {len(initList)}')

        srcMemberDir = modelSetting['srcMemberDir']
        if modelSetting['dataStructure'] == 'mergedGrib2':
            srcFileNames = modelSetting['srcFileNames']
            source = f"{DIRROOT}{lambda2str(srcMemberDir)}{
                lambda2str(srcFileNames)}"
        elif modelSetting['dataStructure'] == 'fakeDmsKey':
            prefix = modelSetting['srcFileNames']['prefix']
            source = f"{DIRROOT}{lambda2str(srcMemberDir)}{lambda2str(prefix)}"

        logging.info(f'{modelName=}')
        logging.info(f'{source=}')
        logging.info(f'   init   start, end = {' to '.join(
            [tt.float2format(t, '%m/%dz%H') for t in [initMin, initMax]])}')

        for init in initList:
            year, month, day, hour = tt.year(init), tt.month(
                init), tt.day(init), tt.hour(init)

            if init in SKIP_INIT or month in SKIP_MONTH:
                logging.info(f'skipping {tt.float2format(init)}')
                continue

            iInitHour = initHours.index(int(hour))
            numMembers = modelSetting['numMembers'][iInitHour]
            leadMaxs = modelSetting['leadMaxs'][iInitHour]

            logging.info(f'    init = {year}/{month}/{day}z{hour:02d}')

            for member in range(numMembers):
                if member in SKIP_MEMBER:
                    logging.info(f'skipping member={member}')
                    continue
                srcDir = DIRROOT + \
                    srcMemberDir(year2d=year % 100, month=month,
                                 day=day, hour=hour, member=member)

                if not os.path.isdir(srcDir):
                    logging.error(f'    X unable to find directory for member = {
                                  member:02d}: {srcDir}')
                    continue

                leadMax = leadMaxs[member]
                logging.info(f'      member = {
                             member:02d}, leadMax = {leadMax:04d}')

                for varName in modelSetting['varNames']:
                    if varName in SKIP_VARNAME:
                        logging.info(f' skipping variable {varName}')
                        continue
                    logging.info(f'      varName = {varName}')
                    
                    if FORCEUPDATE:
                        srcFiles = getSrcFiles()
                    elif not FORCEUPDATE:
                        # Let's check...
                        # If the file is already processed, and the output
                        # number of days is correct, then we can skip it.
                        isCompleted, srcFiles = checkDesFileCompleteness()
                        if isCompleted:
                            continue

                    if len(srcFiles) == 0:
                        logging.error('    XX unable to find any source file')
                        continue
                    mergeFilesToNC(srcFiles)
        return

    def runCommand(cmd, print_command=True, forced_run=False):
        # if not DEBUG:
        #   cmd = cmd + '&> /dev/null'
        if DEBUG or print_command:
            logging.info('[executing] ' + cmd + '\n')
        if forced_run or (not DRYRUN):
            try:
                status, output = subprocess.getstatusoutput(cmd)
            except subprocess.CalledProcessError as e:
                logging.error(f"Error executing command: {e}")
                if DEBUG:
                    exit()
            if DEBUG:
                logging.debug(output)
            return output
        else:
            return None

    def rmMidFile():
        cmd = '/usr/bin/rm ' + MIDFILE
        runCommand(cmd)
        return

    def checkFile(file_to_write):
        if os.path.isfile(file_to_write):
            print(f' file already exists : {file_to_write} ')
            print(' Cowardly exitting the progam')
            exit()
        os.system(f'touch {file_to_write}')
        if not os.access(file_to_write, os.W_OK):
            print(f' Permission denied to write the file: {file_to_write}')
            print(' Sadly exitting the program')
            exit()
        return

    def getGridDes(modelName):
        return DIRROOT + 'griddes/' + modelName + '.txt'
# ====================================================================
# ====================================================================
# ====================================================================
    checkFile(MIDFILE)
    checkFile(LOGFILE)
    for modelName in MODELSETTINGS:
        if not (os.path.isfile(getGridDes(modelName)) or os.path.islink(getGridDes(modelName))):
            logging.error( ' unable to locate grid description file:'
                + f'{getGridDes(modelName)}\n'
                + 'Use cdo o generate a grid description file, for example,\n'
                + '/nwpr/gfs/com120/.conda/envs/rd/bin/cdo griddes SOME_GRIB2_FILE > GIRD_DESCRIPTOR.txt'
            )
            exit()

    # Configure the logging
    logging.basicConfig(
        level=logging.INFO,                      # Set the logging level
        # Define the log format
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(LOGFILE),     # Write to a log file
            logging.StreamHandler()             # Print to the screen
        ]
    )

    logging.info(' begin  getting model data')
    logging.info('')
    logging.info(f' model settings = ')
    logging.info(f' {MODELSETTINGS}')
    logging.info(f'')
    logging.info(f' init min = {tt.float2format(INITMINMAX[0])}')
    logging.info(f' init max = {tt.float2format(INITMINMAX[1])}')
    logging.info(f'')
    logging.info(f' DIRROOT = {DIRROOT}')
    logging.info(f' MIDFILE = {MIDFILE}')
    logging.info(f' LOGFILE = {LOGFILE}')
    logging.info(f'')
    logging.info(f' DEBUG       = {DEBUG}')
    logging.info(f' FORCEUPDATE = {FORCEUPDATE}')
    logging.info(f' DRYRUN      = {DRYRUN}')
    logging.info(f' ')
    logging.info(f' SKIP_MODEL   = {SKIP_MODEL}')
    logging.info(f' SKIP_INIT    = {SKIP_INIT}')
    logging.info(f' SKIP_MONTH   = {SKIP_MONTH}')
    logging.info(f' SKIP_MEMBER  = {SKIP_MEMBER}')
    logging.info(f' SKIP_VARNAME = {SKIP_VARNAME}')
    logging.info('')

    [getOneModel(m) for m in MODELSETTINGS if m not in SKIP_MODEL]

    logging.info(' end getting model data')
# ====================================================================
# ====================================================================
# ====================================================================
    return


def lambda2str(o):
    s = inspect.getsource(o)
    s = ''.join(s.split('lambda')[1:])
    s = ''.join(s.split(':')[1:])
    s = s.replace(' ', '').replace('\n', '').replace(',', '')
    return s
