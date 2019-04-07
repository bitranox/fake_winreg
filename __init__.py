# -*- coding: utf-8 -*-
import logging

try:
    from .lib_registry.lib_registry import *
except ImportError:
    logger = logging.getLogger()
    logger.debug('Import Error - this __init__.py is only meant for local package development')

__title__ = 'lib_registry'
__version__ = '1.0.1'
