# detect test environment and add path for local testing
# this should be the first import in __init__.py
from lib_detect_testenv import *

if is_testenv_active():
    add_path_to_syspath(__file__)

from .fake_winreg import *

from . import __init__conf__

__title__ = __init__conf__.title
__version__ = __init__conf__.version
__name__ = __init__conf__.name
__url__ = __init__conf__.url
__author__ = __init__conf__.author
__author_email__ = __init__conf__.author_email
