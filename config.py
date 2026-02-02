import os
from . import filetools as ft
import json


def load_config(request:str|list[str]) -> str | list | None:
    # loading the configuration json file and return the requested field(s)
    if not isinstance(request, (list, str)):
        raise TypeError('Expecting "request" to be of "str" or "list" type.')

    if isinstance(request, list):
        for r in request:
            if not isinstance(r, str):
                raise TypeError('Expecting elements in "request" to be of "str" type.')

    configPath = get_config_path()
    with open(configPath, 'r') as f:
        config = json.load(f)

    if isinstance(request, list):
        return [config.get(r) for r in request]
    elif isinstance(request, str):
        return config.get(request)




def get_config_path() -> str:
    moduledir = ft.getModuleDirName()

    machine = os.getenv("HOSTNAME")
    specialMachineNames = {
        'gadi-login-01.gadi.nci.org.au': 'gadi-login.json',
        'gadi-login-02.gadi.nci.org.au': 'gadi-login.json',
        'gadi-login-03.gadi.nci.org.au': 'gadi-login.json',
        'gadi-login-04.gadi.nci.org.au': 'gadi-login.json',
        'gadi-login-05.gadi.nci.org.au': 'gadi-login.json',
        'gadi-login-06.gadi.nci.org.au': 'gadi-login.json',
        'gadi-login-07.gadi.nci.org.au': 'gadi-login.json',
        'gadi-login-08.gadi.nci.org.au': 'gadi-login.json',
        'gadi-login-09.gadi.nci.org.au': 'gadi-login.json',
        'gadi-login-10.gadi.nci.org.au': 'gadi-login.json',
        'localhost': 'lorenz',
    }

    defaultFileName = 'template.json'
    fileName = specialMachineNames.get(machine, defaultFileName)

    path = f'{moduledir}/config/{fileName}'
    if os.path.exists(path):
        return path

    raise FileNotFoundError(f'config path not found: {machine=} {path=}')



