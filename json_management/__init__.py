#!/usr/bin/env python3

__all__ = ('JsonManager',)

__version__ = '0.0.1'
VERSION = __version__

from aiotgm.logging import get_logger
logger = get_logger('ujson_manager ' + VERSION)
del get_logger

from .json_management import JsonManager
