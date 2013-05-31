#!/usr/bin/env python3
"""Detchord: bring an application to a halt through constructive destruction"""

from threading import _Semaphore

class Broken(Exception):
    """Breaker has been tripped"""

class RateLimited(Exception):
    """The limiter currently has too many concurrent requests, aborting"""

class Breaker:
    def __init__(self):
        self.reset()
        
    def __enter__(self):
        if not self:
            raise Broken()
        
    def __exit__(self, *tb):
        pass

    def trigger(self):
        self._status = False
        
    def reset(self):
        self._status = True

    def __bool__(self):
        return self._status

class Limiter(_Semaphore):
    def acquire(self):
        if not _Semaphore.acquire(self, False):
            raise RateLimited()
        
    __enter__ = acquire
