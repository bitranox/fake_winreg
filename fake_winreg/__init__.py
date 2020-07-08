from .fake_winreg import PyHKEY
from .fake_winreg import FakeWinReg
from .fake_reg import FakeRegistry
from . import fake_reg
from . import setup_fake_registry

from . import __init__conf__
__title__ = __init__conf__.title
__version__ = __init__conf__.version
__name__ = __init__conf__.name
__url__ = __init__conf__.url
__author__ = __init__conf__.author
__author_email__ = __init__conf__.author_email
