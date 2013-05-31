#!/usr/bin/env python3
"""Timing: Benchmark and Execution time monitoring functions

:py:class:`PrettyTime`: Format a time value (float) for printing as a string
:py:class:`PerfTimer`: Record Time intervals
:py:func:`is_mark`: Test a PerfTimer object to see if it is a mark
:py:func:`is_interval`: Test a PerfTimer object to see if it is an interval

"""
from inspect import isfunction as _isfunction
from functools import wraps as _wraps
from time import time as now
from collections import namedtuple as _namedtuple
import resource as _resource


class PrettyTime(float):
    """Pretty printing time value, behvaes identically to a float
    
    >>> str(PrettyTime(3))
    '3.0S'
    >>> str(PrettyTime(0.003))
    '3.0mS'
    >>> str(PrettyTime(0.000003))
    '3.0uS'
    >>> str(PrettyTime(0.000000003))
    '3.0nS'
    """
    def __format__(self, template):
        s = str(self)
        return s.__format__(template)
        
    def __str__(self):
        val = self
        for unit in ['S', 'mS', 'uS', 'nS']:
            if val >= 1:
                break
            val *= 1000
            
        val = round(val, 2)
        
        return str(val) + unit


class PerfTimer:
    """Record Time intervals and resource usage

    :py:meth:`start`: Start recording a time interval
    :py:meth:`stop`: Stop recording a time interval
    :py:attr:`start_time`: UNIX time of interval start
    :py:attr:`start_resources`: rusage numbers at begning of interval
    :py:attr:`end_time`: UNIX time of interval end
    :py:attr:`end_resources`: rusage numbers at end of interval

    Example:
    ~~~~~~~~
    # Use as a context manager
    >>> timer = PerfTimer('myapp', 'Just for testing')
    >>> with timer('myapp.slowthing') as t:
    ...    pass
    
    # Manual control of timing
    >>> timer = PerfTimer('myapp.Request').start()
    >>> 2+3 #doctest:+SKIP
    >>> timer.stop()
    """
    def __init__(self, name=None, description=None):
        """ 
        :param str name: A name by which to identify the interval
        :param str description: A short description of what is being recorded
        """
        self.name = name
        self.description = description

        self._children = []

        self.start_time = None
        self.start_resources = None
        self.end_time = None
        self.end_resources = None

    def __enter__(self):
        return self.start()
        
    def start(self, name=None, description=None):
        """Begin recording resource usage and time interval
        
        :param str name:
        :param str description:
        :returns: self for use with context managers
        :rtype: PerfTimer
        
        Exceptions
        ~~~~~~~~~~
        :py:exc:`ValueError`: Raised if an interval has already been started
        """
        if self.start_time:
            raise ValueError('PerfTimer already started')
            
        if not name:
            name = self.name
        self.name = name
        
        if description:
            self.description = description
        
        self.start_time = now()
        self.start_resrouces = _resource.getrusage(_resource.RUSAGE_THREAD)

        return self
        
    def __exit__(self, *tb):
        self.stop()
    
    def stop(self):
        """Stop recording resource usage and time interval
        
        Exceptions
        ~~~~~~~~~~
        :py:exc:`ValueError`: Raised if an interval has already been recorded
        """
        if self.end_time:
            raise ValueError('PerfTimer already terminated')

        self.end_time = now()
        self.end_resources = _resource.getrusage(_resource.RUSAGE_THREAD)
    
    def mark(self, name, description=None):
        """Mark a stage or step in an interval without creating multiple PerfTimers
        
        :param str name:
        :param str description:
        """

        mark = self(name, description)
        mark.start()
    
    def __float__(self):
        return self.end_time - self.start_time
        
    def __round__(self, n=0):
        f = self.__float__()
        return round(f, n)
    
    def __int__(self):
        return int(float(self))
    __index__ = __int__

    def __repr__(self):
        if self.end_time:
            interval = PrettyTime(self.end_time - self.start_time)
        else:
            interval = '"Still Running"'

        return '<{}: name: {}, start={:.3F}, interval={}>'.format(self.__class__.__name__, 
                                                                      repr(self.name),
                                                                      self.start_time, 
                                                                      interval,
                                                                     )
    
    def __iter__(self):
        yield self
        for children in self._children:
            for child in children:
                yield child
            
    def __call__(self, name=None, description=None):
        child = self.__class__(name, description)
        self._children.append(child)
        
        return child

    def __len__(self):
        total = 0
        for child in self._children:
            total += len(child)
        
        total += 1
        
        return total

    def __str__(self, event_times=True, interval_times=True):
        """ 
        001 200mS + Request
        002  10mS | + Dependencies
        003  50uS | | + Connect.localhost
        004  10uS | | | + Key in cache?
        005   2mS | | | | + Recalculate Key
        006       | | | | | - Recalculating Key
        007       | | | | | - Key Recalculated, Storing
        008       | | | | =
        009       | | | | - Key Stored
        010       | | | =
        011       | | =
        012       | =
        013   2mS | + Connect.DB (2mS)
        014       | =
        015 130mS | + Render
        016  20mS | | + Render.Header
        017       | | =
        018 100mS | | + Render.Body
        019       | | =
        020   5mS | | + Render.Footer
        021       | | =
        022       | | - Return Status Code: 200 OK
        023       | | - Return Request Headers
        024       | +
        025       +
        """
        marks = []
        events = []
        for event in self:
            if is_mark(event):
                marks.append((event.start_time, event))
            else:
                events.append((event.start_time, event))
                events.append((event.end_time, event))
        
        times = marks + events
        times.sort()
    
        template = ""
        if event_times:
            template += "{time:^14} "
        if interval_times:
            template += "{interval_time:>8} "
        template += "{spacer}{type} {name}{description}"
        
        seen = set()
        depth = 0
        output = []
        old_time = 0
        for time, event in times:
            vars = {'time':0,
                    'interval_time':None,
                    'type':"|",
                    'spacer':"    ",
                    'name':"",
                    'description':"",
                   }
            if event.start_time and not event.end_time:
                # its a mark
                vars['time'] = event.start_time
                vars['name'] = event.name
                vars['description'] = event.description
                vars['type'] = "-"
                vars['spacer'] = "|  " * depth
    
            else:
                # its a period
                if event not in seen:
                    seen.add(event)
                    
                    vars['time'] = event.start_time
                    vars['name'] = event.name
                    vars['description'] = event.description
                    vars['interval_time'] = PrettyTime(float(event))
                    vars['type'] = "+"
                    vars['spacer'] = "|  " * depth
        
                    depth += 1
        
                else:
                    depth -= 1
        
                    vars['time'] = event.end_time
                    vars['type'] = "="
                    vars['spacer'] = "|  " * depth
    
            # pretify time/name/description join
            if '{:10.3F}'.format(old_time) == '{:10.3F}'.format(vars['time']):
                old_time = vars['time']
                vars['time'] = "V"
            else:
                old_time = vars['time']
                vars['time'] = '{time:10.3F}'.format(**vars)
            vars['description'] = ": " + vars['description'] if vars['description'] else ""
            vars['interval_time'] = PrettyTime(vars['interval_time']) if vars['interval_time'] else ""
            output.append(template.format(**vars))
                
        return '\n'.join(output)

    
def is_mark(timer):
    """Test if the supplied timer object is a Mark

    :param PerfTimer timer: Timer object to test
    :rtype: bool
    """
    return timer.start_time and not timer.end_time


def is_interval(timer):
    """Test if the supplied timer object is an Interval

    :param PerfTimer timer: Timer object to test
    :rtype: bool
    """
    return not (timer.start_time and not timer.end_time)
