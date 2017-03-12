# Author: Michel Pelletier


from rdflib.plugins.memory import randid
from rdflib.store import Store
from rdflib import BNode

from persistent import Persistent
from persistent.dict import PersistentDict
from itertools import chain

import BTrees

ANY = Any = None
DEFAULT = BNode(u'ZODBStore:DEFAULT')

# TODO:
#   * is zope.intids id search faster? (maybe with large dataset and actual
#     disk access?)
#   * compare BTree intersect to builtin set operation (needs reduce)
#   * compare against BDB with disk access


class ZODBStore(Persistent, Store):

    context_aware = True
    formula_aware = True
    graph_aware = True

    family = BTrees.family32

    def __init__(self, configuration=None, identifier=None, family=None):
        super(ZODBStore, self).__init__(configuration, identifier)
        if family is not None:
            self.family = family
        self.__namespace = self.family.OO.BTree()
        self.__prefix = self.family.OO.BTree()
        self.__int2obj = self.family.IO.BTree()
        self.__obj2int = self.family.OI.BTree()
        # subject index key: sid val: enctriple
        self.__subjectIndex = self.family.IO.BTree()
        # predicate index key: pid val: enctriple
        self.__predicateIndex = self.family.IO.BTree()
        # object index key: oid val: enctriple
        self.__objectIndex = self.family.IO.BTree()
        self.__tripleContexts = self.family.OO.BTree()
        self.__all_contexts = self.family.OO.TreeSet()
        self.__defaultContexts = None

    def bind(self, prefix, namespace):
        self.__prefix[namespace] = prefix
        self.__namespace[prefix] = namespace

    def namespace(self, prefix):
        return self.__namespace.get(prefix, None)

    def prefix(self, namespace):
        return self.__prefix.get(namespace, None)

    def namespaces(self):
        for prefix, namespace in self.__namespace.iteritems():
            yield prefix, namespace

    def add(self, triple, context, quoted=False):
        # oldlen = len(self)
        Store.add(self, triple, context, quoted)
        context = getattr(context, 'identifier', context)
        if context is None:
            context = DEFAULT
        if context is not DEFAULT and context not in self.__all_contexts:
            self.__all_contexts.add(context)

        enctriple = self.__encodeTriple(triple)
        sid, pid, oid = enctriple

        cid = self.__obj2id(context)
        self.__addTripleContext(enctriple, cid, quoted)

        if sid in self.__subjectIndex:
            self.__subjectIndex[sid].add(enctriple)
        else:
            self.__subjectIndex[sid] = self.family.OO.Set((enctriple,))

        if pid in self.__predicateIndex:
            self.__predicateIndex[pid].add(enctriple)
        else:
            self.__predicateIndex[pid] = self.family.OO.Set((enctriple,))

        if oid in self.__objectIndex:
            self.__objectIndex[oid].add(enctriple)
        else:
            self.__objectIndex[oid] = self.family.OO.Set((enctriple,))

    def remove(self, triplepat, context=None):
        context = getattr(context, 'identifier', context)
        if context is None:
            context = DEFAULT
        defid = self.__obj2id(DEFAULT)
        req_cid = self.__obj2id(context)
        for triple, contexts in self.triples(triplepat, context):
            enctriple = self.__encodeTriple(triple)
            for cid in self.__getTripleContexts(enctriple):
                if context is not DEFAULT and req_cid != cid:
                    continue
                self.__removeTripleContext(enctriple, cid)

            ctxs = self.__getTripleContexts(enctriple, skipQuoted=True)
            if defid in ctxs and (context is DEFAULT or len(ctxs) == 1):
                self.__removeTripleContext(enctriple, defid)
            if len(self.__getTripleContexts(enctriple)) == 0:
                # triple has been removed from all contexts
                sid, pid, oid = enctriple
                self.__subjectIndex[sid].remove(enctriple)
                self.__predicateIndex[pid].remove(enctriple)
                self.__objectIndex[oid].remove(enctriple)

                del self.__tripleContexts[enctriple]

        if triplepat == (None, None, None) and \
                context in self.__all_contexts and \
                not self.graph_aware:
            # remove the whole context but not empty graphs
            self.__all_contexts.remove(context)

    def triples(self, triplein, context=None):
        context = getattr(context, 'identifier', context)
        if context is not None:
            if context == self:  # hmm...does this really ever happen?
                context = None
        if context is None:
            context = DEFAULT

        cid = self.__obj2id(context)
        enctriple = self.__encodeTriple(triplein)
        sid, pid, oid = enctriple

        # all triples case (no triple parts given as pattern)
        if sid is None and pid is None and oid is None:
            return self.__all_triples(cid)

        # optimize "triple in graph" case (all parts given)
        if sid is not None and pid is not None and oid is not None:
            if sid in self.__subjectIndex and \
               enctriple in self.__subjectIndex[sid] and \
               self.__tripleHasContext(enctriple, cid):
                return ((triplein, self.__contexts(enctriple)) for i in [0])
            else:
                return self.__emptygen()

        # remaining cases: one or two out of three given
        sets = []
        if sid is not None:
            if sid in self.__subjectIndex:
                sets.append(set(self.__subjectIndex[sid]))
            else:
                return self.__emptygen()
        if pid is not None:
            if pid in self.__predicateIndex:
                sets.append(set(self.__predicateIndex[pid]))
            else:
                return self.__emptygen()
        if oid is not None:
            if oid in self.__objectIndex:
                sets.append(set(self.__objectIndex[oid]))
            else:
                return self.__emptygen()

        # to get the result, do an intersection of the sets (if necessary)
        if len(sets) > 1:
            # BTrees intersection: reduce(intersection, sets)
            enctriples = sets[0].intersection(*sets[1:])
        else:
            enctriples = sets[0].copy()  # OOSet(sets[0])

        return ((self.__decodeTriple(enctriple), self.__contexts(enctriple))
                for enctriple in enctriples
                if self.__tripleHasContext(enctriple, cid))

    def contexts(self, triple=None):
        if triple is None or triple is (None, None, None):
            return (context for context in self.__all_contexts)

        enctriple = self.__encodeTriple(triple)
        sid, pid, oid = enctriple
        if ((sid in self.__subjectIndex and
             enctriple in self.__subjectIndex[sid])):
            return self.__contexts(enctriple)
        else:
            return self.__emptygen()

    def __len__(self, context=None):
        context = getattr(context, 'identifier', context)
        if context is None:
            context = DEFAULT
        cid = self.__obj2id(context)
        return sum(1 for enctriple, contexts in self.__all_triples(cid))

    def add_graph(self, graph):
        if not self.graph_aware:
            Store.add_graph(self, graph)
        else:
            self.__all_contexts.add(graph)

    def remove_graph(self, graph):
        if not self.graph_aware:
            Store.remove_graph(self, graph)
        else:
            self.remove((None, None, None), graph)
            try:
                self.__all_contexts.remove(graph)
            except KeyError:
                pass  # we didn't know this graph, no problem

    def __addTripleContext(self, enctriple, cid, quoted):
        """add the given context to the set of contexts for the triple"""
        defid = self.__obj2id(DEFAULT)

        sid, pid, oid = enctriple
        if ((sid in self.__subjectIndex and
             enctriple in self.__subjectIndex[sid])):
            # we know the triple exists somewhere in the store
            if enctriple not in self.__tripleContexts:
                # triple exists with default ctx info
                # start with a copy of the default ctx info
                self.__tripleContexts[
                    enctriple] = self.__defaultContexts.copy()

            self.__tripleContexts[enctriple][cid] = quoted
            if not quoted:
                self.__tripleContexts[enctriple][defid] = quoted
        else:
            # the triple didn't exist before in the store
            if quoted:  # this context only
                self.__tripleContexts[enctriple] = PersistentDict(
                    {cid: quoted})
            else:   # default context as well
                self.__tripleContexts[enctriple] = PersistentDict(
                    {cid: quoted, defid: quoted})

        # if this is the first ever triple in the store, set default ctx info
        if self.__defaultContexts is None:
            self.__defaultContexts = self.__tripleContexts[enctriple]

        # if the context info is the same as default, no need to store it
        if self.__tripleContexts[enctriple] == self.__defaultContexts:
            del self.__tripleContexts[enctriple]

    def __getTripleContexts(self, enctriple, skipQuoted=False):
        """return a list of (encoded) contexts for the triple, skipping
           quoted contexts if skipQuoted==True"""

        ctxs = self.__tripleContexts.get(enctriple, self.__defaultContexts)

        if not skipQuoted:
            return ctxs.keys()

        return [cid for cid, quoted in ctxs.iteritems() if not quoted]

    def __tripleHasContext(self, enctriple, cid):
        """return True iff the triple exists in the given context"""
        ctxs = self.__tripleContexts.get(enctriple, self.__defaultContexts)
        return (cid in ctxs)

    def __removeTripleContext(self, enctriple, cid):
        """remove the context from the triple"""
        ctxs = self.__tripleContexts.get(
            enctriple, self.__defaultContexts).copy()
        del ctxs[cid]
        if ctxs == self.__defaultContexts:
            del self.__tripleContexts[enctriple]
        else:
            self.__tripleContexts[enctriple] = ctxs

    def __obj2id(self, obj):
        """encode object, storing it in the encoding map if necessary, and
           return the integer key.

           New identifiers are generated in such a way as to increase the
           chance that identifers added at the same time will be clustered
           closer together in the btree. This relies on the assumption that
           data added within a single run of a program is likelier to be
           accessed together at a later time than other data.
        """
        if obj is None:
            return None
        if obj not in self.__obj2int:
            if not hasattr(self, '_v_next_id'):
                self._v_next_id = randid()
            new_id = self._v_next_id
            while new_id in self.__int2obj:
                new_id += randid()
            self._v_next_id = new_id + 1
            self.__obj2int[obj] = new_id
            self.__int2obj[new_id] = obj
            return new_id
        return self.__obj2int[obj]

    def __makeSlices(self, items, thresh=100000, single_serving=False):
        if not single_serving:
            items = sorted(items)
            _min = items[0]
            _last = items[0]
            for cur in items:
                if _last - cur > thresh:
                    yield (_min, _last)
                    _min = cur
                _last = cur
            yield(_min, _last)
        else:
            yield (min(items), max(items))

    def __exo(self, index, triple, context, tidx, aidx, bidx):
        target = triple[tidx]
        cid = self.__obj2id(context)
        if len(target) == 1:
            triple = tuple(s[0] if s == target else s for s in triple)
            return self.triples(triple, context)
        elif len(target) == 0:
            triple = tuple(None if s == target else s for s in triple)
            return self.triples(triple, context)
        else:
            results = set()
            aid = self.__obj2id(triple[aidx])
            bid = self.__obj2id(triple[bidx])
            obj_ids = list(self.__multiple_obj2id(target))

            slices = self.__makeSlices(obj_ids, single_serving=True)
            for min_id, max_id in slices:
                items = dict(index.iteritems(min=min_id, max=max_id))
                for y in obj_ids:
                    if aid is None and bid is None:
                        results.add(items[y])
                    elif aid is None:
                        results.add(z for z in items[y] if z[bidx] == bid)
                    elif bid is None:
                        results.add(z for z in items[y] if z[aidx] == aid)
                    else:
                        results.add(z for z in items[y]
                                    if (z[aidx] == aid and z[bidx] == bid))
            return ((self.__decodeTriple(enctriple),
                     self.__contexts(enctriple))
                    for enctriples in results
                    for enctriple in enctriples
                    if self.__tripleHasContext(enctriple, cid))

    def triples_choices(self, triple, context=None):
        context = getattr(context, 'identifier', context)
        if context is not None:
            if context == self:
                context = None
        if context is None:
            context = DEFAULT

        subject, predicate, object_ = triple
        if isinstance(object_, list):
            assert not isinstance(
                subject, list), "object_ / subject are both lists"
            assert not isinstance(
                predicate, list), "object_ / predicate are both lists"
            if object_:
                return self.__exo(self.__objectIndex, triple, context, 2, 0, 1)
            else:
                return self.triples((subject, predicate, None), context)

        elif isinstance(subject, list):
            assert not isinstance(
                predicate, list), "subject / predicate are both lists"
            if subject:
                return self.__exo(self.__subjectIndex, triple, context,
                                  0, 1, 2)
            else:
                return self.triples((None, predicate, object_), context)

        elif isinstance(predicate, list):
            assert not isinstance(
                subject, list), "predicate / subject are both lists"
            if predicate:
                return self.__exo(self.__predicateIndex, triple, context,
                                  1, 0, 2)
            else:
                return self.triples((subject, None, object_), context)

    def __multiple_obj2id(self, objs):
        slices = list(self.__makeSlices(objs, single_serving=True))
        items_list = []
        for least_obj, greatest_obj in slices:
            items = dict(self.__obj2int.iteritems(min=least_obj,
                                                  max=greatest_obj))
            items_list.append(items[j] for j in objs)
        return chain(*items_list)

    def __id2obj(self, id):
        if id is None:
            return None
        return self.__int2obj[id]

    def __encodeTriple(self, triple):
        """encode a whole triple, returning the encoded triple"""
        return tuple(map(self.__obj2id, triple))

    def __decodeTriple(self, enctriple):
        """decode a whole encoded triple, returning the original triple"""
        return tuple(map(self.__id2obj, enctriple))

    def __all_triples(self, cid):
        """return a generator which yields all the triples (unencoded) of
           the given context"""
        for tset in self.__subjectIndex.values():
            for enctriple in self.family.OO.Set(tset):  # copy
                if self.__tripleHasContext(enctriple, cid):
                    yield (self.__decodeTriple(enctriple),
                           self.__contexts(enctriple))

    def __contexts(self, enctriple):
        """return a generator for all the non-quoted contexts (unencoded)
           the encoded triple appears in"""
        return (self.__id2obj(cid) for cid
                in self.__getTripleContexts(enctriple, skipQuoted=True)
                if cid is not DEFAULT)

    def __emptygen(self):
        """return an empty generator"""
        if False:
            yield
