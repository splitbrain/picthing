# -*- coding: utf-8 -*-

import os
import re
import whoosh
import whoosh.index
import whoosh.fields
import whoosh.qparser

from Metadata import Metadata

class Indexer:

    index    = None
    root     = None
    writer   = None
    searcher = None

    def __init__(self, root):
        self.root = os.path.abspath(root)
        idxdir = os.path.join(self.root,".index")

        if(whoosh.index.exists_in(idxdir)):
            # index exists, load it
            print "loading index in "+idxdir
            self.index = whoosh.index.open_dir(idxdir)
        else:
            # new index, create it
            print "creating index in "+idxdir
            if(not os.path.exists(idxdir)):
                os.mkdir(idxdir)
            self.index = whoosh.index.create_in(idxdir, schema=self.get_schema())

        self.writer   = self.index.writer()
        self.searcher = self.index.searcher()

    def close(self):
        print "closing index"
        del self.writer
        del self.searcher
        self.index.close()
        del self.index

    def get_schema(self):
        return whoosh.fields.Schema(
            path    = whoosh.fields.ID(unique=True, stored=True),
            folder  = whoosh.fields.TEXT,
            time    = whoosh.fields.STORED,
            title   = whoosh.fields.TEXT(stored=True),
            content = whoosh.fields.TEXT,
            tags    = whoosh.fields.KEYWORD(stored=True, lowercase=True, commas=True, scorable=True),
        )

    def scan_root(self):
        imgre = re.compile('\.jpe?g$',re.IGNORECASE)

        for directory, subdirs, files in os.walk(self.root):
            for fn in files:
                if(not imgre.search(fn)):
                    continue

                filepath = os.path.join(directory,fn)
                relpath  = os.path.relpath(filepath,self.root)
                folder   = os.path.dirname(relpath)

                meta = Metadata(filepath)
                print meta.get_content()

                # add to index
                self.writer.update_document(
                    path    = unicode(relpath),
                    folder  = unicode(folder),
                    time    = os.path.getmtime(filepath),
                    title   = meta.get_content(),
                    content = meta.get_title(),
                    tags    = meta.get_tags()
                    #FIXME add more EXIF data here
                )

        # save index
        self.writer.commit()

    def search(self,query):
        mparser = whoosh.qparser.MultifieldParser(["title", "content"], schema=self.get_schema())
        results = self.searcher.search(mparser.parse(query));
        return results

