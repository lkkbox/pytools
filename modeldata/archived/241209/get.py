'''
2024/12/05 lkkbox

source file name =   DIRROOT + srcMemberDir + srcFileNames
DESDIR  = DIRROOT + 'processed/{modelName}/20{year2d:02d}/{month:02d}/{day:02d}z{hour:02d}/E{member:03d}/'

DIRROOT/griddes/
DIRROOT/processed/

'''
from .. import timetools as tt
from ..plottools import FlushPrinter as Fp
from ..nctools import getVarShape as getNcVarShape
import os
import subprocess
import inspect
import logging
from .setup import getVarSettings


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
):

    def getOneModel(modelName):
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
                        break

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
                    break
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

            if varSetting['levelType'] == 'surface':
                numEntries = 1
            elif varSetting['levelType'] == 'pressure':
                numEntries = len(varSetting['levels'])

            griddes = getGridDes(modelName)
            desDir = getDesDir()

            desFile_global = getDesFile_global()
            desFile_WNP = getDesFile_WNP()
            doWNP = varSetting['levelType'] == 'surface'

            # cat to one grib2 file
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

                    # counting the number of entries retreived by wgrib2 matches the number of levels
                    cmd_getEntries = f'{wgrib2} {
                        srcFile} -match "({modelSetting['grib2Keys'][varName](lead)})"'
                    result = runCommand(
                        cmd_getEntries, print_command=False, forced_run=True)
                    if result is None:  # no output by wgrib2
                        logging.error(f'FAIL: recieved 0 entries:\n  command = {
                                      cmd_getEntries}\n,  entries = None')
                        break
                    else:
                        entries = result.split('\n')
                    if len(entries) != numEntries:
                        logging.error(f'FAIL: recieved {len(entries)} entries:\n  command = {
                                      cmd_getEntries}\n  {entries=}')
                        break

                    # The entry check is passed. Now extract the record and append to MIDFILE
                    cmd = f'{cmd_getEntries} -append -grib {MIDFILE}'
                    runCommand(cmd, print_command=DEBUG)

            print('', end='\n', flush=True)
            logging.info(' catting files done!')

            if not os.path.isfile(MIDFILE):
                logging.error(
                    f'FAIL: no output files from cattting grib2 files')
                return  # todo make a error message here

            # create destination folder
            if not os.path.isdir(desDir):
                runCommand(f'mkdir -p {desDir}')

            # cdo options
            cdoVarName = modelSetting['cdoVarName'][varName]
            hourShift = modelSetting['hourShift'][varName]
            multiplyConstant = modelSetting['multiplyConstant'][varName]

            setTimeAxis = f'-settaxis,{year}-{month}-{day},12:00:00,1day'
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
            if FORCEUPDATE or (not os.path.isfile(desFile_global)):
                cmd = cdo
                cmd += f' {preSelectRegion}'
                cmd += f' -remapbil,r360x180'
                cmd += f' {postSelectRegion}'
                cmd += f' {MIDFILE} {desFile_global}'
                runCommand(cmd)
                logging.info(f'file done: {desFile_global}')

            # WNP: cdo remap, daymean
            if (doWNP and not os.path.isfile(desFile_WNP)) or (doWNP and FORCEUPDATE):
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
            d + h/24 for h in initHours for d in range(int(initMin), int(initMax)+1)][::-1]
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

                for varName, varSetting in varSettings.items():
                    if varName in SKIP_VARNAME:
                        logging.info(f' skipping variable {varName}')
                        continue
                    logging.info(f'      varName = {varName}')
                    
                    if not FORCEUPDATE:
                        # check if the file is already processed.
                        desFile_global = getDesFile_global()
                        desFile_WNP = getDesFile_WNP()
                        existingNT_global = getNcVarShape(getDesFile_global(), varName)[0]
                        existingNT_WNP = getNcVarShape(getDesFile_WNP(), varName)[0]
                        doWNP = varSetting['levelType'] == 'surface'
                        lastLead = modelSetting['leadList'][varName][-1]
                        if leadMax > lastLead:
                            lastLead = leadMax
                        numDays = 1 + int(lastLead/24) #ceiling

                        # global only
                        if existingNT_global == numDays and (not doWNP):
                            logging.info(
                                f' The des file is found, skipped. ({desFile_global} with {numDays = })')
                            continue

                        # global and WNP
                        if existingNT_global == numDays and existingNT_WNP == numDays:
                            logging.info('The des file is found, skipped.'
                                        + f'({desFile_global} and {desFile_WNP}'
                                        + f' with {numDays = }'
                            )
                            continue

                    if modelSetting['dataStructure'] == 'fakeDmsKey':
                        srcFiles = getSrcFiles_fakeDmsKey()
                    if modelSetting['dataStructure'] == 'mergedGrib2':
                        srcFiles = getSrcFiles_mergedGrib2()

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

    varSettings = getVarSettings()
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
