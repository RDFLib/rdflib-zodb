# Author: Michel Pelletier

Any = None

from rdflib.plugins.memory import IOMemory
# you must export your PYTHONPATH to point to a Z2.8 or Z3+ installation to 
# get this to work!, like: export PYTHONPATH="/home/michel/dev/Zope3Trunk/src"

from persistent import Persistent

from BTrees.IOBTree import IOBTree
from BTrees.OIBTree import OIBTree
from BTrees.OOBTree import OOBTree, OOTreeSet

class ZODBGraph(Persistent, IOMemory):

    def __init__(self, configuration=None, identifier=None):
        super(ZODBGraph, self).__init__(configuration, identifier)
        self.__namespace = OOBTree()
        self.__prefix = OOBTree()
        self.__int2obj = IOBTree()
        self.__obj2int = OIBTree()
        self.__subjectIndex = IOBTree() # key: sid val: enctriple
        self.__predicateIndex = IOBTree() # key: pid val: enctriple
        self.__objectIndex = IOBTree() # key: oid val: enctriple
        self.__tripleContexts = OOBTree()
        self.__all_contexts = OOTreeSet()
