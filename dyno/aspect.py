#!/usr/bin/env python3
"""aspect: Enhance functions/methods by wrapping the function with a pipeline of functions at runtime
to iterativly enhance the call. The idea presented here is similar to aspects from spring python and 
roughly equivalent to a 'join point' with part of the dependency injection built-in and adapted for the
dyno registration framework

>>> registry = {}
>>> @advertise('mymodule.func', registry)
... def test(a, b, c):
...     return a+b+c
>>> registry
{'mymodule.func': []}
>>> test(1,1,1)
3

# Define our transforms
>>> def add_one(*args, **kwargs):
...     new_args = []
...     for arg in args:
...         new_args.append(arg+1)
...     return new_args, kwargs

>>> def const(val):
...     def wrapped(a, b, c, *args, **kwargs):
...         b = val
...         return (a,b,c) + args, kwargs
...     return wrapped

# now we register a pipeline of transforms
>>> registry['mymodule.func'] = [add_one, const(15)]
>>> test(1,1,1) # gets transformed to (2,15,2)
19

"""
from functools import wraps as _wraps
import logging as _logging

log = _logging.getLogger('dyno.aspect')

def advertise(name, registry=None): # XXX TODO: if registry == None, load default registry
    """Advertise function at <name> on <registry> so that a pipeline of cuntions can be plugged in
    
    args/kwargs -> pipeline[func1 -> func2 -> func3] -> decorated_func -> result
    
    :param str name: The name to advertise the funciton at
    :param Registry registry: The registry to register the name on
    :returns: function wrapper
    :rtype: func
    """
    def outer_wrapper(wrapped_func):
        """Lifetime: Function Defeinition"""
        registry[name] = []
        log.info('Registered join point "%s"', wrapped_func)
        
        @_wraps(wrapped_func)
        def inner_wrapper(*args, **kwargs):
            """Lifetime: When Targeted Function is Called"""
            pipeline = registry[name]
            for func in pipeline:
                args, kwargs = func(*args, **kwargs)
            
            return wrapped_func(*args, **kwargs)
            
        return inner_wrapper
    return outer_wrapper
