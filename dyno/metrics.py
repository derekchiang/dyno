#!/usr/bin/env python3
"""Metrics: Collect and report statistics over a short period of time"""
from time import time as now
from bisect import bisect_right as _bisect

MINUTES = 60
HOURS = 60 * MINUTES

class Metrics:
    def __init__(self, traffic_span=2*MINUTES, latency_span=1*MINUTES, counters_span=10):
        """ 
        :param float span: collect statistics for the last N seconds
        """
        self.traffic_span = traffic_span
        self.latency_span = latency_span
        self.counters_span = counters_span
        
        self.succeeded = []
        self.failed = []
        
    def success(self):
        n = now()
        self.succeeded.append(n)
        i = _bisect(self.succeeded, n - self.counters_span)
        self.succeeded = self.succeeded[i:]
        
    def failure(self):
        n = now()
        self.failed.append(n)
        i = _bisect(self.failed, n - self.counters_span)
        self.failed = self.failed[i:]

    @property
    def graph(self):
        """ 
        return a list of 0.0 to 1.0 that represent the relative change in 
        traffic over the time period
        """

    @property
    def request_rate(self):
        """ 
        :returns: the ammount of requests per second
        :rtype: int
        """

    @property
    def error_rate(self):
        """ 
        :returns: the ammount of errors per second
        :rtype: int
        """

    @property
    def successes(self):
        pass
        
    @property
    def short_circuits(self):
        pass
        
    @property
    def thread_timeouts(self):
        pass
        
    @property
    def pool_rejections(self):
        pass
        
    @property
    def failures(self):
        pass
        

    def __enter__(self):
        timer = PerfTimer()
        self.timers.append(timer)
        
        return timer
        
    def __exit__(self, *tb):
        if tb:
            if tb == Broken:
                self.short_cuircuit()
            elif tb == PoolFull:
                self.pool_full()
        else:
            self.sucess()

# timer functionatlity
#    def mean(self):
#    def median(self):
#    def percentile90(self):
#    def percentile95(self):
#    def percentile99(self):
#    def percentile995(self):
