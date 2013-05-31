#!/usr/bin/env python3
"""Registry: global object registry

Allows obtaining a handle to an object before the objects concrete implementation 
is accsessable at the location specified. this can be used to allow a function
to specify its dependencies and have these dependencies filled in at a latter time
AFTER the handle is obtained but BEFORE the function is used (eg in the 'setup'
phase of a program ie 'definition', 'setup', 'execution')

>>> reg = Registry()
>>> def test_func(obj=reg['my_obj']):
...     return bool(obj)
>>> test_func()
Traceback (most recent call last):
  File ...
dyno.registry.NotRegistered: The key: "my_obj" has not yet been registered

>>> reg['my_obj'] = True
>>> test_func()
True
"""

from collections import UserDict as _UserDict
import logging as _logging

log = _logging.getLogger('dyno.registry')

class Registry(_UserDict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.get = self.data.get
        
    def __dir__(self):
        keys = self.__dict__.keys()
        keys.update(self.data)
        
        return keys

    def simple_get(self, key):
        """same as get but explodes with an exception if key is not found
        like original obj[key] syntax
        """
        class NoKey(object):
            """Dummy hidden class so we don't trip up on returned default value
            when object has been set but is the same as the default value as this
            object is only guaranteed to exist in the current block/scope
            """
            pass

        obj = self.get(key, NoKey)
        if obj is NoKey:
            raise KeyError(key)
            
        return obj

    def __missing__(self, key):
        log.debug('Could not find key: %s in self: %s, returning proxy', key, self)
        return RegistryProxy(self, key)

class NotRegistered(Exception):
    """The key: "{}" has not yet been registered"""
    def __str__(self):
        return self.__doc__.format(self.args[0])

def proxy_object_methods(obj):
    """Proxy most built in special function calls so that the proxy object
    acts as much as possible like the real concrete object, such that they 
    can be used interchangably in most cases
    """
    methods = ['call', 'str', 'int', 'bytes', 'format',
               'lt', 'le', 'eq', 'ne', 'gt', 'ge', 'hash',
               'bool', 'instancecheck', 'subclasscheck',
               'add', 'radd', 'iadd', 'mul', 'rmul', 'imul',
               'contains', 'iter', 'len', 'reversed', 
               'sub', 'rsub', 'isub', 'div', 'rdiv', 'idiv',
               'truediv', 'floordiv', 'mod', 'divmod', 'pow',
               'lshift', 'rshift', 'and', 'or', 'xor', 
               'rtruediv', 'rfloordiv', 'rmod', 'rdivmod', 'rpow',
               'rlshitf', 'rrshift', 'rand', 'ror', 'rxor',
               'itruediv', 'ifloordiv', 'imod', 'ipow', 
               'ilshift', 'irshift', 'iand', 'ior', 'ixor',
               'neg', 'pos', 'abs', 'invert', 'complex',
               'float', 'round', 'index', 'enter', 'exit',
              ]
               

    template = "__{}__"
    for method in methods:
        method = template.format(method)
        def proxy_builder(method):
            def proxy(self, *args, **kwargs):
                obj = self._getobj()
                func = getattr(obj, method)
                
                return func(*args, **kwargs)
            return proxy

        setattr(obj, method, proxy_builder(method))
   
    return obj
   
@proxy_object_methods
class RegistryProxy:
    def __init__(self, registry, key):
        self.__dict__['_registry'] = registry
        self.__dict__['_key'] = key
    
    # make object introspectable in standard python shells
    def __dir__(self):
        try:
            attrs = dir(self._getobj())
        except NotRegistered:
            attrs = []
        
        return attrs
    
    def _getobj(self):
        try:
            return self._registry.simple_get(self._key)
        except KeyError as err:
            raise NotRegistered(self._key) from err

    ## Attribute proxy methods ##
    def __getattr__(self, key):
        return getattr(self._getobj(), key)
    def __setattr__(self, key, val):
        setattr(self._getobj(), key, val)
    def __delattr__(self, key):
        delattr(self._getobj(), key)

    ## Mapping proxy methods ##
    def __getitem__(self, key):
        return self._getobj()[key]
    def __setitem__(self, key, val):
        self._getobj()[key] = val
    def __delitem__(self, key):
        del self._getobj()[key]

    ## Call proxy methods ##
    def __call__(self, *args, **kwargs):
        self._getobj()(*args, **kwargs)

    def __repr__(self):
        return '<RegistryProxy: "{}" on {}>'.format(self._key, self._registry)

