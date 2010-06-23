# -*- coding: utf-8 -*-

from Indexer import Indexer
from Metadata import Metadata

x = Indexer("test")
schema = x.get_schema()
print schema


x.scan_root()


print str(x.index.doc_count()) + " documents in the index"

