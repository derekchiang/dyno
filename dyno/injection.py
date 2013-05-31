#!/usr/bin/env python3
"""Injection: Dependency injection functions

:py:decorator:`inject`: injection mechnism that uses explicit naming of kwargs passed 
                        into the decorator and thier values to detirmine what to inject
                        and where. relies on the default values in the actual function
                        for fallback values
:py:decorator:`inject3`: injection mechanism that uses function annotations and default 
                         values to inject values
:py:func:`socket`: A wrapper/constructor around socket.socket and socket.connect to create
                   a connection to a remote server for injection. also serves as an example
                   implementation of a dependency
:py:data:`log_dependency`: logging.Logger object so that depndencies can all log to the same
                           location and be filtered for easily

Below are some time constants to be used as the timeout value for :py:func:`socket`
* :py:const:`LOCALHOST_TIMEOUT`: Timeout value for services on localhost
* :py:const:`LAN_TIMEOUT`: Timeout value for services on LAN
* :py:const:`DC_TIMEOUT`: Timeout value for services on multihop LAN (same site by 
                          transiting over multiple hops)
* :py:const:`INTERNET_TIMEOUT`: Timeout value for responsive sites on the internet

Issues
'''''''
* in some cases you may want to inject a constructor function into a function but 
  have a static values such as an int or None as the fallback. in this case it is 
  recommend that the fallback value be wrapped in a lambda with the same number or
  arguments as the constructor so that code does not explicitly have to check to 
  see if it has the default value or a function and dispatch to code handling 
  Either case but instead it can just call the lambda in the same way as the 
  constructor and get the expected value
"""
from dyno.retry import retry as _retry, CompoundException as _CompoundException
from functools import wraps as _wraps
import logging as _logging
import socket as _socket
import inspect as _inspect

# Several preset timeout values for convenience
LOCALHOST_TIMEOUT = 0.05
LAN_TIMEOUT = 0.05
DC_TIMEOUT = 0.2
INTERNET_TIMEOUT = 3

log = _logging.getLogger('dyno.injection')
# seperate log file for dependencies
log_dependency = _logging.getLogger('dependencies')

def inject(**dep_kwargs):
    """.. py:decorator:: inject(**kwargs)
    
    Inject dependencies into an object
    
    inject allows you to wrap a function in a constructor that when called will build 
    the specified dependencies from their constructors and inject them into the wrapped
    object Either directly by the constructor or indirectly via the kwargs in a callable
    function
    
    in the latter form mentioned above, inject performs a similar function to 
    functools.partial with the difference being that the partially applied kwargs are 
    constructed when the object is called and not when the object is wrapped
    
    in the case where the dependencies are injected via kwargs, specifying the same kwarg
    when calling the wrapped function as is specified in the inject decorator will cause
    the argument supplied in the function call and not the kwarg supplied in inject to 
    take precedence, allowing overriding of dependencies on a per call basis
    
    :param dict kwargs: A dictionary of dependencies to fill in in the wrapped function
                        the value of each key will be executed to build the dependency
                        and then placed into the wrapped functions kwargs with the same 
                        key.
    :returns:  A wrapped function
    :rtype:    func
    """
    def wrapped(obj):
        log.info("Found object for injection: %s, injecting: %s", obj, dep_kwargs)
        def build_deps():
            kwargs = {}
            for key, dep in dep_kwargs.items():
                try:
                    dep = dep(obj, key)
                    kwargs[key] = dep
                except Exception as err:
                    log.info('{} dependency (key="{}") raised an exception, '
                             'using default value. exception: {}'.format(obj, key, err)) 
            return kwargs
            
        if _inspect.isfunction(obj):
            # Indirect injection (Builder)
            @_wraps(obj)
            def call(*args, **kwargs):
                new_kwargs = build_deps()
                new_kwargs.update(kwargs)
                
                return obj(*args, **new_kwargs)

            return call
        else:
            # Direct injection
            attrs = build_deps()
            for key, val in attrs.items():
                setattr(obj, key, val)
            
            return obj

    return wrapped

def inject3(func):
    """Special python3 version of :py:function:`inject()` that uses function argument
    annotations to specifiy injections instead of specifying them in :py:function:`inject()`
    kwargs
    
    Example:
    >>> @inject3
    ... def test(a:lambda x,y:3, b:lambda x,y:4):
    ...     return (a, b)
    >>> test()
    (3, 4)

    # example of default args being used in place of function that has failed
    >>> def fail(request, key):
    ...     raise ValueError("Everyday i'm Error'ing")
    >>> @inject3
    ... def test(a:3, b:fail=4):
    ...     return (a, b)
    >>> test(3)
    (3, 4)
    """
    log.info("Found object for injection: %s, injecting: %s", func, func.__annotations__)
    @_wraps(func)
    def call(*args, **kwargs):
        new_kwargs = {}
        
        for key, dep in func.__annotations__.items():
            try:
                dep = dep(func, key)
                new_kwargs[key] = dep
            except Exception as err:
                log.info('{} dependency (key="{}") raised an exception, '
                         'using default value. exception: {}'.format(func, key, err)) 
        new_kwargs.update(kwargs)
        
        return func(*args, **new_kwargs)
    return call

def socket(domain, port, # address settings
           family=_socket.AF_UNSPEC, type=_socket.SOCK_STREAM, proto=_socket.IPPROTO_IP, # connection type
           timeout=LAN_TIMEOUT, retries=1): # connection policy
    """socket: a factory for socket connections to a remote server and an example of a dependency to be injected
    
    :param str domain: The domain or ip to connect to
    :param int port: The port number or service name to connect to
    :param family: The address family to use (Default: AF_UNSPEC)
    :type family: socket.AF_*
    :param type: The socket type to use eg DGRAM, STREAM, SEQPACKET (Default: SOCK_STREAM)
    :type type: socket.SOCK_*
    :type proto: socket.IPPROTO_*
    :param timeout: Ammount of time to wait in seconds before abandoning the connection and 
                    trying another server
    :type timeout: int or float
    :param int retries: The number of times to retry to connect to the server. note that if 
                        multiple records exisst for the domain the server will try them each 
                        in turn before retyring the same connection in an attempt to avoid 
                        using an overloaded server
    :returns: Factory function for buildign a socket connection
    :rtype: function
    """
    def constructor(request, key):
        addresses = _socket.getaddrinfo(domain, port, family, type, proto)
        try:
            @_retry(retries)
            def block():
                for *args, name, addr in addresses:
                    try:
                        s = _socket.socket(*args)
                        s.settimeout(timeout)
                        s.connect(addr)
                        
                        return s
                    except _socket.error as err:
                        continue
        except _CompuoundException as err:
            log.debug('Recived compound exception while connecting to %s:%d (%s)',domain, port, err)
            raise IOError('Could not connect to %s:%d', domain, port)
    return constructor

