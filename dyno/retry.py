#!/usr/bin/env python3
"""Retry: Automatically handle re-execution of a code if the code raises an exception"""
from collections import OrderedDict as _OrderedDict
from functools import wraps as _wraps
import logging as _logging

log = _logging.getLogger('dyno.retry')

def uniq(l):
    # we want to use an ordered dict here instead of a set to preserve order
    dict = _OrderedDict.fromkeys(l)

    return list(dict.keys())

class CompoundException(Exception):
    """For use with retry(), is a base class for a dynamically created exception
    that is the compisition of this class/exception and the last raised exception
    so that 'normal' exception handling code sees the object it expects while
    more robust exception handlers can pull out all exceptions that lead to a failure
    and process them as they like
    """
    def __init__(self, errors, *args, **kwargs):
        self._errors = errors
        # Even though we have multiple inheritance here we DO NOT call super
        # as the multiple inheritence is designed to fit into exisiting
        # exception handling mechanisms, ie this is a Polymorphic Excption, one
        # that imitates all its children Exceptions and acts as a container for them
        # so normal code can stay unchanged while CompoundException aware code can 
        # handle each exception individually
        #
        # so basically we only really need to call Exception to get the behavior
        # one would normmaly expect when creating an exception (ie args provided
        # become the error message)
        Exception(self, *args, **kwargs)
        
    def __iter__(self):
        return iter(self._errors)
        
    def __len__(self):
        return len(self._errors)

    def __repr__(self):
        errors = [repr(e) for e in self._errors]
        errors = ", ".join(errors)
        name = 'CompoundException({})'.format(errors)

        return name

def make_compound_exception(errors, *args, **kwargs):
    """Builds an Exception/Class on the fly that is a subclass of all provided exceptions
    
    :param errors: All Exception Instances to be included
    :type errors: list of Exceptions
    :param args:   Arguments to pass to the generated class
    :param kwargs: Keyword arguments to pass to the generated class
    :returns: a Custom class that is a subclass of all provided exceptions and CompoundException
    :rtype: Subclass of all errors and Exception
    
    Note: as the class is dynamically generated, 2 instances will not compare equal
    eg:
    >>> cls1 = make_compound_exception([ValueError()])
    >>> cls2 = make_compound_exception([ValueError()])
    >>> cls1 == cls2
    False
    
    in practive this should not be an issue but if it is required let the author know as
    it is not as simple as memoizing based on the args (which are instances of Exceptions
    not Exception classes) and hence would have the same issue as indicated above
    """
    name = 'CompoundException'
    bases = [CompoundException] + [e.__class__ for e in errors]
    bases = uniq(bases)
    bases = tuple(bases)
    exc = type(name, bases, {})

    return exc(errors, *args, **kwargs)
        
def retry(times, *args, **kwargs):
    """ 
    :param int times: the ammount of times to retry the function call
    :param args: args to pass to the wrapped function
    :param kwargs: kwargs to pass to wrapped function
    :returns: value of func(*args, **kwargs)
    """
    
    def wrapped(func, execute=True):
        """ 
        :param func func: Function to be wrapped
        :param bool execute: (optional) if True (the default) the function will be calculated
                             'lazily', ie when its called. otherwise this function will 
                             execute as soon as its defined (greedy) making the passed in
                             function simmilar to a scope or anon function
        :returns: Return value of func(*args, **kwargs) or Wrapped function to call latter, 
                  you may use the earlier bound args and kwargs or specify them again when 
                  calling the function
        """
        @_wraps(func)
        def wrapper(*args, **kwargs):
            errors = []
            for i in range(times):
                try:
                    return func(*args, **kwargs)
                except Exception as err:
                    log.debug('%s raised an exception (%s) on attempt %d/%d', func, err, i+1, times)
                    errors.append(err)
            
            log.debug('%s failed %d times, aborting', func, times)
            # All retry attempts failed, pass ALL exception
            # upstream for handling
            compound_err = make_compound_exception(errors)
            raise compound_err from errors[-1]
            
        if execute:
            return wrapper(*args, **kwargs)
        else:
            return wrapper
            
    return wrapped
    
#@retry(3, 1,2,3,a=3)
#@transaction
#def anon(*args):
#    for arg in args:
#        db[arg] = None
