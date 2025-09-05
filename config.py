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
    machine = os.getenv("HOSTNAME")
    moduledir = ft.getModuleDirName()
    path = f'{moduledir}/config/{machine}.json'
    if os.path.exists(path):
        return path

    path = f'{moduledir}/config/template.json'
    if os.path.exists(path):
        return path

    raise FileNotFoundError(f'config path not found: {machine=} {path=}')



