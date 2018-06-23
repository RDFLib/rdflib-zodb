#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import re

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


# Find version. We have to do this because we can't import it in Python 3 until
# its been automatically converted in the setup process.
def find_version(filename):
    _version_re = re.compile(r'__version__ = "(.*)"')
    for line in open(filename):
        version_match = _version_re.match(line)
        if version_match:
            return version_match.group(1)


def doc(s):
    res = []
    front = ''
    for l in s.split('\n'):
        if not front:
            mo = re.match(r'\s+', l)
            if mo:
                front = mo.group(0)
        l = l.replace(front, '', 1)
        res.append(l)
    return '\n'.join(res)


__version__ = find_version('pow_zodb/__init__.py')

PY2 = sys.version_info.major == 2


setup(
    name='pow-store-zodb',
    version=__version__,
    description="rdflib extension adding ZODB as back-end store. Forked from rdflib-zodb",
    author="Mark Watts",
    author_email="wattsmark2015@gmail.com",
    url="http://github.com/openworm/rdflib-zodb",
    license="BSD",
    platforms=["any"],
    tests_require=[
        'tox',
        'pytest>=3.4.0',
        'pytest-cov==2.5.1',
        'discover==0.4.0',
    ] + (['mock==2.0.0'] if PY2 else []),
    long_description=doc("""
    ZOPE Object Database implementation of rdflib.store.Store.

    This store has been adapted for use with PyOpenWorm, but it is acceptable
    for general use.
    """),
    classifiers=["Programming Language :: Python",
                 "Programming Language :: Python :: 2",
                 "Programming Language :: Python :: 2.7",
                 'Programming Language :: Python :: 3',
                 'Programming Language :: Python :: 3.4',
                 'Programming Language :: Python :: 3.6',
                 'Programming Language :: Python :: Implementation :: PyPy',
                 "License :: OSI Approved :: BSD License",
                 "Topic :: Software Development :: Libraries :: Python Modules",
                 "Operating System :: OS Independent",
                 "Natural Language :: English",
                 ],
    packages=["pow_zodb"],
    test_suite="test",
    install_requires=["rdflib >= 4.1.0", "BTrees", 'ZODB>=5.4.0', "transaction"],
    entry_points={
        'rdf.plugins.store': [
            'ZODB = pow_zodb.ZODB:ZODBStore',
        ],
    }
)
