import pathlib
from .lib_registry import *


def get_version():      # type: ignore
    with open(pathlib.Path(__file__).parent / 'version.txt', mode='r') as version_file:
        version = version_file.readline()
    return version


__title__ = 'lib_registry'
__version__ = get_version()    # type: ignore
__name__ = 'lib_registry'
