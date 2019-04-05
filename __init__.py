# -*- coding: utf-8 -*-

# this is only for local development when the package is actually not installed
try:
    from .lib_registry.lib_registry import *
except ImportError:
    pass

__title__ = 'lib_registry'
__version__ = '1.0.1'
