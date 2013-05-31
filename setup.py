#!/usr/bin/env python

name = 'dyno'
path = 'dyno'


## Automatically determine project version ##
from setuptools import setup, find_packages
try:
    from hgdistver import get_version
except ImportError:
    def get_version():
        d = {}
        with open(path + "/__init__.py") as f:
            try:
                exec(f.read(), None, d)
            except:
                pass
    
        return d.get("__version__", 0.1)

## Use py.test for "setup.py test" command ##
from setuptools.command.test import test as TestCommand
class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = [path, 'tests']
        self.test_suite = True
    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        pytest.main(self.test_args)

## Try and extract a long description ##
for readme_name in ("README", "README.rst", "README.md"):
    try:
        readme = open(readme_name).read()
    except (OSError, IOError):
        continue
    else:
        break
else:
    readme = ""

## Finally call setup ##
setup(
    name = name,
    version = get_version(),
    packages = [path], 
    author = "Da_Blitz",
    author_email = "code@pocketnix.org",
    maintainer=None,
    maintainer_email=None,
    description = "Dependency injection framework based of Netflix's Hystrix",
    long_description = readme,
    license = "MIT BSD",
    keywords = "DI dependency injection framework hystrix guice",
    download_url='http://code.pocketnix.org/dyno/archive/tip.tar.bz2',
    classifiers=None,
    platforms=None,
    url = "http://code.pocketnix.org/dyno",
    zip_safe = True,
    setup_requires = ['hgdistver'],
    install_requires = ['distribute'],
    tests_require = ['pytest'],
    cmdclass = {'test': PyTest},
)
