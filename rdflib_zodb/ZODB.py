# Author: Michel Pelletier

Any = None

from rdflib.plugins.memory import IOMemory
# you must export your PYTHONPATH to point to a Z2.8 or Z3+ installation to
# get this to work!, like: export PYTHONPATH="/home/michel/dev/Zope3Trunk/src"

try:
    # Zope 3
    from persistent import Persistent
    assert Persistent
except ImportError:
    # < Zope 2.8?
    from Persistence import Persistent
    assert Persistent

from BTrees.IOBTree import IOBTree
from BTrees.OIBTree import OIBTree
from BTrees.OOBTree import OOBTree


class ZODBGraph(Persistent, IOMemory):
    context_aware = True

    def createForward(self):
        return IOBTree()

    def createReverse(self):
        return OIBTree()

    def createIndex(self):
        return IOBTree()

    def createPrefixMap(self):
        return OOBTree()
