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
    imgre    = None
    scan     = False

    def __init__(self, root):
        self.imgre = re.compile('\.jpe?g$',re.IGNORECASE)
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


    def close(self):
        print "closing index"
        del self.writer
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

    def scan_start(self):
        """ Prepare directory scanning. Run this before running the
            scan iterator
        """
        self.writer = self.index.writer()
        self.scan   = True

    def scan_stop(self):
        """ Finish (or interrupt) a directory scan """
        if self.writer:
            print "index committed"
            self.writer.commit()
            del self.writer
        self.scan   = False

    def scan_iterator(self,base,onloop=None, onexit=None):
        """ Iterate over all found images in the given base directory
            and below and add them to the index

            this is designed to be run from gobject.idle_add()

            before starting this, you need to call scan_start()

            scan_stop() is called automatically, but can also be used
            to interupt the scan

            base    - the full path of the directory to scan
            onloop  - callback to run on each loop:
                      func(path, isimage)
            onexit  - callback when the run finishes or is aborted:
                      func(wasabort)
        """

        for directory, subdirs, files in os.walk(base):
            for fn in files:
                if not self.scan:
                    if(callable(onexit)):
                        onexit(True)
                    self.scan_stop()
                    yield False

                filepath = os.path.join(directory,fn)
                isimage = self.imgre.search(fn);

                if(callable(onloop)):
                    onloop(filepath, isimage)

                if(isimage):
                    self.update_image(filepath)

                yield True

        # we're through - stop the run
        if(callable(onexit)):
            onexit(False)
        self.scan_stop()
        yield False


    def update_image(self,filepath):
        """ Adds or updates the given image in the index

            Set commit to False and call index.commit() yourself
            when doing batch operations
        """
        relpath  = os.path.relpath(filepath,self.root)
        folder   = os.path.dirname(relpath)

        meta = Metadata(filepath)

        if not self.writer:
            self.writer = self.index.writer()
            commit      = True
        else:
            commit      = False

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

        if(commit):
            self.writer.commit()
            del self.writer


    def search(self,query):
        searcher = self.index.searcher()
        mparser = whoosh.qparser.MultifieldParser(["title", "content", "tags"], schema=self.get_schema())
        results = searcher.search(mparser.parse(query));
        return results

