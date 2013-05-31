#!/usr/bin/env python3
"""Service: Remote services framework
"""

class PoolFull(Exception):
    pass

class Pool:
    def __enter__(self):
        raise PoolFull()

    def __exit__(self):
        pass
        
# execution of command sync or async
# is the circuit open?
# is the thread pool/queue/semaphore full
# run command
# command timeout? => fallback()
# command sucsessful? else fallback()
# sucsessfule response? log metrics and report, => response
# failed response? => log, partially trip breaker => fallback
# calculate circuit health

def service(builder, metrics=None, breaker=None, pool=None):
    if not metrics:
        metrics = Metrics()
    if not circuit:
        breaker = Breaker()
    if not pool:
        pool = Pool()

    def check_metrics()
        if metrics.failed_too_offten:
            breaker.trigger()

    def wrapped():
        with metrics:
            with breaker, pool:
                val = builder()
                log.info('all OK')
                return val
