#!/usr/bin/env python3

__all__ = ('JsonManager',)

__version__ = '1.0.1'
VERSION = __version__

from apitele.logging import get_logger
logger = get_logger('manage_json ' + VERSION)
del get_logger

from .manage_json import JsonManager
