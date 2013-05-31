#!/usr/binenv python3
"""Utils: useful utility functions"""
import logging as _logging

log = _logging.getLogger('dyno.utils')

def percentile(percent, data):
    """Determine the N'th Percentile of a list
    
    :param int percent: the percentile of the data you are interested in. e.g. 99 for 99%
    :param list data: data for calculateing the percentile
    :returns: returns element N from passed in data where N represents the entry of the
              percentile element
    :rtype: int
    
    >>> percentile(99, list(range(100)))
    99
    
    >>> percentile(50, list(range(100)))
    50
    
    """
    pos = len(data) * (percent/100)
    pos = int(pos)
    
    data = data[:]
    data.sort()
    
    return data[pos]
