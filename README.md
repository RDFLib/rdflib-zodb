ZOPE Object Database implementation of rdflib.store.Store.

The boilerplate ZODB/ZEO handling has been wrapped up in a utility class, ZODBGraph

The implementation replaces the internal data structures of rdflib
IOMemory store with ZODB based BTree structures. Therefore any
structural change in rdflib's IOMemory implementation makes it
incompatible with already persisted stores.

(e.g. rdflib 3 and rdflib 4 stores are incompatible)

[![Build Status](https://travis-ci.org/openworm/rdflib-zodb.png?branch=master)](https://travis-ci.org/openworm/rdflib-zodb)
[![Coverage Status](https://coveralls.io/repos/openworm/rdflib-zodb/badge.png)](https://coveralls.io/r/openworm/rdflib-zodb)
[![Latest Version](https://pypip.in/v/pow-store-zodb/badge.png)](https://pypi.python.org/pypi/pow-store-zodb/)
[![Downloads](https://pypip.in/d/pow-store-zodb/badge.png)](https://pypi.python.org/pypi/pow-store-zodb/)
[![License](https://pypip.in/license/pow-store-zodb/badge.png)](https://pypi.python.org/pypi/pow-store-zodb/)
