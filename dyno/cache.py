#!/usr/bin/env python3
"""Cache: a automated caching layer"""

from collections import MutableMapping as _MutableMapping
from inspect import getargspec as _getargspec
from itertools import chain as _chain
from functools import wraps as _wraps
from random import random as _random
from time import time as now
import logging as _logging

log = _logging.getLogger('dyno.cache')

MINUTES = 60
HOURS = MINUTES * 60
DAYS = HOURS * 24

class BaseCache(_MutableMapping):
    """Base class of all cache backends"""
    def __contains__(self, key):
        pass
        
    def __getitem__(self, key):
        pass

    def __setitem__(self, key, val):
        pass
        
    def __delitem__(self, key):
        pass

class DictCache(dict):
    __slots__ = ()
    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, dict.__repr__(self))

def cache(backend, keys=[], lifetime=None):
    """Cache the output of a function based on the keys specified in keys for the specified lifetime
    
    :param backend: The cache backend to cache values in, subclass of :py:class:`BaseCache`
    :type backend: A Cache backend
    :param keys: The keys of the args in the funciton to cache on. if the list is 
                 empty or not specified then all keys will be used
    :type keys: list of strings
    :param lifetime: If an int/float, the ammount of time the object is valid for 
                     before being cached. if a callable, call the function on each 
                     request and if False is returned, recalculate the value 
                     and reprime the cache. if None, cache the value forever.
    :type lifetime: int/float or callable or None
    """
    def outer(func):
        # we use lifetime_func here so we don't shadow the global
        # and get a 'referenced before assignment' error
        if isinstance(lifetime, (int, float)):
            lifetime_func = static_timeout(lifetime)
        else:
            lifetime_func = lifetime
        
        argspec = _getargspec(func)

        cacheable_keys = keys
        if not keys:
            cacheable_keys = argspec.args
        
        @_wraps(func)
        def inner(*args, **kwargs):
            # as zip terminates as soon as one iterator is exausted we dont
            # have to worry about the case where some args are specified and
            # some use thier default value as the len(args) (ie the specified 
            # args) will cause automatic termination
            args_mapping = zip(argspec.args, args)
            
            cache_keys = []
            for key, item in _chain(args_mapping, kwargs.items()):
                if key in cacheable_keys:
                    cache_keys.append((key, item))
            # lists are unhashable and cant be used as dict keys
            cache_keys.sort()
            cache_keys = tuple(val for key, val in cache_keys)
            
            recalculate = False
            cached = backend.get(cache_keys)
            if cached:
                expiry, output = cached
                expire = lifetime_func(expiry)
                if expire:
                    recalculate = True
            else:
                recalculate = True
                    
            if recalculate:
                output = func(*args, **kwargs)
                expiry = lifetime_func()
                backend[cache_keys] = expiry, output

            return output
        return inner
    return outer

def static_timeout(timeout):
    """Recache the value after a specifed ammount of time has passed"""
    def wrapped(expiry=None):
        if expiry is None:
            # we want the next expiry
            return now() + timeout
        else:
            # we want to know if we should expire and its expiry time
            start = expiry - timeout
            cache = now() + timeout if expiry < now() else False
            return cache
    return wrapped


def linear_timeout(timeout):
    """Increase the chances of the value being recalculated as time goes by ina linear fashion

    100% | NO   /
         |CACHE/|
         |    / |
         |   /  |
         |  /   | <-- timeout
         | /    |
         |/CACHE|
      0% +------|----
         0  Time -->
    """
    def wrapped(expiry=None):
        if expiry is None:
            # we want the next expiry
            return now() + timeout
        else:
            # we want to know if we should expire and its expiry time
            start = expiry - timeout
            delta = now() - start
            threshold = delta/timeout
            cache = last + timeout if _random() < threshold else False
            return cache
    return wrapped

def exponential_timeout(timeout, exponent=2):
    """Expontentially increase the chances of the value being recalculated

    100% |             |
         |             |
         |DO NOT CACHE||
         |           / |
         |          /  | <-- timeout
         |   ___---`   |
         |---  CACHE   |
      0% +-------------|-
         0  Time -->
    """
    def wrapped(expiry=None):
        if expiry is None:
            # we want the next expiry
            return now() + timeout
        else:
            # we want to know if we should expire and its expiry time
            start = expiry - timeout
            delta = now() - start
            val = delta/timeout
            threshold = val ** exponent
            cache = last + timeout if _random() < threshold else False
            return cache
    return wrapped
