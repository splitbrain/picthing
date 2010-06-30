""" Manage the ListStore behind the main icon view and all related functions

    * file system browsing
    * querying the index
    * thumbnailing
"""

import os
import gtk
import re
import gobject

from Indexer import Indexer;
from GeneratorTask import GeneratorTask;


class FileManager:
    COL_TITLE  = 0
    COL_PATH   = 1
    COL_PIXBUF = 2
    COL_TYPE   = 3

    store = None
    root  = None
    index = None

    thumbnailer = None

    def __init__(self,root):
        self.store = gtk.ListStore(str, str, gtk.gdk.Pixbuf, str)
        self.root  = os.path.abspath(root)
        self.index = Indexer(self.root)

    def search(self,query):
        """ Search the index for the given query

            query needs to be something the Whoosh query parser can parse,
            otherwise Whoosh exceptions are bubbled up
        """
        self.stop_thumbnailer()
        self.store.clear()
        results = self.index.search(unicode(query))

        for i, fields in enumerate(results):
            title = fields['title']
            if(title == ''):
                title = os.path.basename(fields['path']);

            self.store.append([
                title,
                fields['path'],
                self.get_icon(gtk.STOCK_FILE),
                'jpg'])
        self.start_thumbnailer()


    def browse(self,folder):
        """ Browse the given folder

        folder needs to exist and be relative to the library root,
        otherwise a NoDirException is thrown
        """
        self.stop_thumbnailer()
        self.store.clear()

        folder = folder.replace('..','')
        full = os.path.join(self.root,folder)
        full = os.path.abspath(full)
        imgre = re.compile('\.jpe?g$',re.IGNORECASE)

        if(not os.path.isdir(full)):
            raise NoDirException("No such directory in library: "+folder)

        # add upper dir
        if(folder):
            upper = os.path.dirname(folder);
            self.store.append([
                        '..',
                        upper,
                        self.get_icon(gtk.STOCK_GO_UP),
                        'dir'])

        for fl in os.listdir(full):
            if fl[0] == '.':
                continue; #skip hidden files

            fn    = os.path.join(full,fl)
            rel   = os.path.relpath(fn,self.root)
            title = os.path.basename(fn)

            if(os.path.isdir(fn)):
                self.store.append([
                    title,
                    rel,
                    self.get_icon(gtk.STOCK_DIRECTORY),
                    'dir'])
            elif(imgre.search(fn)):
                self.store.append([
                    title,
                    rel,
                    self.get_icon(gtk.STOCK_FILE),
                    'jpg'])
        self.start_thumbnailer()


    def start_thumbnailer(self):
        """ Start thumbnailing for the current ListStore

            Thumbnailing is done in a separate thread
        """
        self.stop_thumbnailer()
        self.thumbnailer = GeneratorTask(self._create_thumbnails)
        self.thumbnailer.start()

    def stop_thumbnailer(self):
        """ Stop any running thumbnailer

            Always call this before the ListStore is cleared!
        """
        if self.thumbnailer is not None:
            self.thumbnailer.stop()
            self.thumbnailer.wait()
            self.thumbnailer = None

    def _create_thumbnails(self):
        """ The thumbnailing process

            FIXME: reading addtional image info from exif might be
            sensible here
        """
        for row in self.store:
            path  = row[self.COL_PATH]
            ftype = row[self.COL_TYPE]
            fn    = os.path.join(self.root,path)
            if(ftype == 'jpg'):
                buf = gtk.gdk.pixbuf_new_from_file_at_size(fn, 48, 48)
                row[self.COL_PIXBUF] = buf
            yield None


    def get_itemat(self,pos):
        row = self.store[pos];
        path  = row[self.COL_PATH]
        ftype = row[self.COL_TYPE]
        fn    = os.path.join(self.root,path)

        return {'fn':fn, 'ft': ftype}

    def get_nextimagepos(self,pos):
        """ Get the position of the next image (not dir) after the given
            position. If the given positon is None, the search sats at the
            beginning of the store

            FIXME there is probably a much more elegant way doing the
            whole iteration stuff, but I can't figure it out
        """
        if(pos == None):
            pos = 0;
        else:
            pos = pos+1;

        try:
            rowiter = self.store.get_iter(pos);
            while rowiter != None:
                if(self.store.get_value(rowiter,self.COL_TYPE) == 'jpg'):
                    return self.store.get_path(rowiter)[0];
                self.store.iter_next(rowiter);
        except ValueError: # we're out of range
            pass
        return None

    def get_previmagepos(self,pos):
        """ Get the position of the next image (not dir) before the given
            position.

            FIXME there is probably a much more elegant way. And I have no
            idea how to iterate backwards anyway
        """
        while (pos >=0):
            pos -= 1;
            try:
                rowiter = self.store.get_iter(pos);
                if(self.store.get_value(rowiter,self.COL_TYPE) == 'jpg'):
                    return self.store.get_path(rowiter)[0];
            except ValueError: # we're out of range
                pass
        return None


    def get_icon(self, name):
        """ Helper to load a stock icon
        """
        theme = gtk.icon_theme_get_default()
        return theme.load_icon(name, 48, 0)


class NoDirException (StandardError):
    pass
