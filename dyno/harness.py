#!/usr/bin/env python3
"""Harness: An Error/Exception reporting framework
"""
from functools import wraps as _wraps
import logging as _logging

def harness(logger=_logging.getLogger('dyno.harness')):
    """decorator to log any exceptions occuring in function and re-raise them
    
    :param logging.Logger logger: logger function to log to. this implementation
                                  only calls logger.exception and any compatible 
                                  object that provides this method will work
    """
    def outer_wrapper(func):
        @_wraps(func)
        def inner_wrapper(*args, **kwargs):
            try:
                ret = func(*args, **kwargs)
                return ret
            except Exception as err:
                logger.exception('Exception in %s', func)
                raise # let other functions handle this
        return inner_wrapper
    return outer_wrapper
