from rdflib import plugin
from rdflib import store

# Support execution of nosetests without actual installation
plugin.register(
        'ZODB', store.Store,
        'pow_zodb.ZODB', 'ZODBStore')
