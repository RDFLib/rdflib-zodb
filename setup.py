#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import re
from setuptools import setup
try:
    import multiprocessing
    assert multiprocessing
except Exception:
    pass


# Find version. We have to do this because we can't import it in Python 3 until
# its been automatically converted in the setup process.
def find_version(filename):
    _version_re = re.compile(r'__version__ = "(.*)"')
    for line in open(filename):
        version_match = _version_re.match(line)
        if version_match:
            return version_match.group(1)


__version__ = find_version('rdflib_zodb/__init__.py')

config = dict(
    name='rdflib-zodb',
    version=__version__,
    description="rdflib extension adding ZODB as back-end store",
    author="Graham Higgins",
    author_email="gjhiggins@gmail.com",
    url="http://github.com/RDFLib/rdflib-zodb",
    # download_url="https://github.com/RDFLib/rdflib-zodb/zipball/master",
    license="BSD",
    platforms=["any"],
    long_description="""
    ZOPE Object Database implementation of rdflib.store.Store.

    The boilerplate ZODB/ZEO handling has been wrapped up in a utility
    class, ZODBStore """,
    classifiers=["Programming Language :: Python",
                 'Programming Language :: Python :: 3',
                 'Programming Language :: Python :: 3.8',
                 'Programming Language :: Python :: Implementation :: PyPy',
                 "License :: OSI Approved :: BSD License",
                 "Topic :: Software Development :: Libraries :: Python Modules",
                 "Operating System :: OS Independent",
                 "Natural Language :: English",
                 ],
    packages=["rdflib_zodb"],
    test_suite="test",
    install_requires=["rdflib >= 4.1.0", "BTrees"],
    entry_points={
        'rdf.plugins.store': [
            'ZODB = rdflib_zodb.ZODB:ZODBStore',
        ],
    }
)

setup(**config)
