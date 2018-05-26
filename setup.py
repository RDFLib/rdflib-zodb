#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import re
try:
    import multiprocessing
    assert multiprocessing
except:
    pass


def setup_python3():
    # Taken from "distribute" setup.py
    from distutils.filelist import FileList
    from distutils import dir_util, file_util, util, log
    from os.path import join

    tmp_src = join("build", "src")
    log.set_verbosity(1)
    fl = FileList()
    for line in open("MANIFEST.in"):
        if not line.strip():
            continue
        fl.process_template_line(line)
    dir_util.create_tree(tmp_src, fl.files)
    outfiles_2to3 = []
    for f in fl.files:
        outf, copied = file_util.copy_file(f, join(tmp_src, f), update=1)
        if copied and outf.endswith(".py"):
            outfiles_2to3.append(outf)

    util.run_2to3(outfiles_2to3)

    # arrange setup to use the copy
    sys.path.insert(0, tmp_src)

    return tmp_src


# Find version. We have to do this because we can't import it in Python 3 until
# its been automatically converted in the setup process.
def find_version(filename):
    _version_re = re.compile(r'__version__ = "(.*)"')
    for line in open(filename):
        version_match = _version_re.match(line)
        if version_match:
            return version_match.group(1)

__version__ = find_version('pow_zodb/__init__.py')

config = dict(
    name='pow-store-zodb',
    version=__version__,
    description="rdflib extension adding ZODB as back-end store. Forked from rdflib-zodb",
    author="Mark Watts",
    author_email="wattsmark2015@gmail.com",
    url="http://github.com/mwatts/pow-store-zodb",
    license="BSD",
    platforms=["any"],
    long_description="""
    ZOPE Object Database implementation of rdflib.store.Store.

    The boilerplate ZODB/ZEO handling has been wrapped up in a utility
    class, ZODBStore """,
    classifiers=["Programming Language :: Python",
                 "Programming Language :: Python :: 2",
                 "Programming Language :: Python :: 2.7",
                 'Programming Language :: Python :: 3',
                 'Programming Language :: Python :: 3.4',
                 'Programming Language :: Python :: Implementation :: PyPy',
                 "License :: OSI Approved :: BSD License",
                 "Topic :: Software Development :: Libraries :: Python Modules",
                 "Operating System :: OS Independent",
                 "Natural Language :: English",
                 ],
    packages=["pow_zodb"],
    test_suite="test",
    install_requires=["rdflib >= 4.1.0", "BTrees"],
    entry_points={
        'rdf.plugins.store': [
            'ZODB = pow_zodb.ZODB:ZODBStore',
        ],
    }
)

if sys.version_info[0] >= 3:
    from setuptools import setup
    config.update({'use_2to3': True})
    config.update({'src_root': setup_python3()})
else:
    try:
        from setuptools import setup
    except ImportError:
        from distutils.core import setup


setup(**config)
