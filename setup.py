from setuptools import setup

setup(
    name = 'rdflib-zodb',
    version = '0.1',
    description = "rdflib extension adding ZODB as back-end store",
    author = "Graham Higgins",
    author_email = "gjhiggins@gmail.com",
    url = "http://github.com/RDFLib/rdflib-zodb",
    py_modules = ["rdflib_zodb"],
    test_suite = "test",
    install_requires = ["rdflib>=3.0", "rdfextras>=0.1", "Persistence"],
    entry_points = {
    	'rdf.plugins.store': [
            'ZODB = rdfextras.store.ZODB:ZODBGraph',
        ],
    }

)
