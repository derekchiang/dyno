# Dyno

## Intro

This is a fork from [dyno 0.2](https://pypi.python.org/pypi/dyno/).  This document was originally written by the original author.  Any significant changes I made are written in this form: (EDIT: my words).

Dyno is a set of libraries for implementing fault tolerant service orientated architectures based off the [Hystrix](https://github.com/Netflix/Hystrix) library for Java from Netflix. Inspiration has also been taken from the [Spring Python Project](http://springpython.webfactional.com/) for the JVM and Google's [Guice](http://code.google.com/p/google-guice/) project for dependency injection.

The library itself is split into separate modules with no dependencies between any of the modules and is intended to be used in a 'mix and match' fashion, using only what you need. (EDIT: some dependencies between modules might be established in the future)

# Module List

* aspect.py

  Iteratively enhance a function call by passing the arguments and the return value through a series of filter functions.

  This is basically syntactic sugar as it could be done with decorators but has seen use as a separate module in a web framework called `xing` to handle things like automatic templating, ETAG generation and if-modified handling.

* breaker.py
  
  `breaker` allows you to install re-settable fuses or breakers in your application that can be triggered to shut of requests to that function.  This could be used to short circuit requests to a CPU expensive function in high load situations or to enable and disable features (e.g. in an A/B testing situation or having features disabled in production until they are tested).

* cache.py
  
  `cache` allows you to cache objects and retire them probabilistically to avoid dog piling of requests. instead on each request there is an (increasing) chance that the function will be recalculated and the cache updated, avoiding a situation where the cache expires and multiple threads end up recalculating the same value.

* harness.py

  `harness` allows you to 'pull out' any exceptions that occur and log them without affecting the exception so that components Further up the call chain can still intercept them.

  This can be handy if you are trying to locate a transient failure or look at how often a component such as the cache or a socket connection 'errors out'
  
* injection.py
  
  A dependency injection framework that is used for slightly different purposes than a traditional dependency injection library. the goal of this library is to move the construction of objects from inside the function body to the function definition instead. in addition it is designed to handle the case where the object construction fails by either providing a fallback value such as None, or by error'ing out and raising an exception.
  
  This makes the function more declarative and helps to enable easier testing by reducing the need for mocking. in addition it can be used to declare multiple 'expensive' objects as dependencies (such as an open connection to a server on the other side of the planet) and execute the 'construction' of all these dependencies in parallel when combined with a worker pool (TODO: make a lib 
  for this).
  
* metrics.py
  
  Provides a Metrics object that allow the recording of statistics such as the latency, amount of requests in flight and the rate of exceptions for function calls. modeled closely after the Hystrix equivalent and management frontend.
  
* registry.py
  
  A registry for providing runtime resolution of services. this allows you to put off determining 'what' until the moment you need it by not naming the exact class of what you need but instead choosing a tag in the registry and asking for the object it represents when you need it. This provides a unified way to have your code reference something and have other (setup?) code fill in these references for you (e.g. from a config file).

  It can also be used to change the object at runtime.

  This is mainly useful in situations with the dependency code above as you can simply register the dependency in the registry and swap in the provider of that dependency as part of your programs' start-up / initialization.
  
  While it is possible to just add values to objects to modules or even class definitions, using a registry allows you to not have to keep track of who actually uses the registered value and having to update them all manually. In the case of adding an object to a module, having a registry allows you to have 'instances' of the registry which may be helpful in vhosting type situations (no global registry object)
  
* retry.py

  This module provides a retry object which will attempt to execute the supplied function multiple times BEFORE raising an exception. the exception that ends up getting raised will be a Union of all the exceptions raised for use with try/except blocks as well as being a instance of CompoundExeption for code that is specifically written to handle multiple exceptions in a single 'raise'
  
  This is mainly for dependency injection of things such as socket connections where you may want to try and connect to the other end multiple times before failing but can also be used as a decorator on an inline declared function (as a pseudo anonymous function) to have that code attempted multiple times (e.g. a database transaction) see the documentation in /docs for an example or the comments in the module
  
* service.py
  
  An attempt to pull together the Worker Pool logic described above and mix it with the Metrics, Breaker and retry code in one convenient object to be used as a decorator so that a dependency to a 'service' can be written as a function that makes a single attempt to resolve or construct that dependency and have the logic behind retrying / aborting / logging provided by the `dyno` library.
  
* timing.py
  
  Provides a timing object that collects info on 'events' and 'intervals' and can print them out for providing diagnosis information and insight as to the run-time of code
  
  Supports explicit marking of events and intervals via a start/stop mechanism or with an 'with' statement.
  
  Passing the timing object up and down the functions on a per request basis is 
  left as an exercise to the reader.
  
* utils.py
  
  Various bits and ends that currently don't belong elsewhere, currently only holds functions for stats generation.

## Status

This project is in its early stages and not yet in production, API changes may be significant and are not guaranteed to be stable until a `v1.0` release. Use at your own risk however please feel free to steal the ideas in this project.