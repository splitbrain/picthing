
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
        self.root  = root
        self.index = Indexer(self.root)

    def search(self,query):
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
        self.stop_thumbnailer()
        self.thumbnailer = GeneratorTask(self._create_thumbnails)
        self.thumbnailer.start()

    def stop_thumbnailer(self):
        if self.thumbnailer is not None:
            self.thumbnailer.stop()
            self.thumbnailer.wait()
            self.thumbnailer = None

    def _create_thumbnails(self):
        for row in self.store:
            path  = row[self.COL_PATH]
            ftype = row[self.COL_TYPE]
            fn    = os.path.join(self.root,path)
            if(ftype == 'jpg'):
                buf = gtk.gdk.pixbuf_new_from_file_at_size(fn, 48, 48)
                row[self.COL_PIXBUF] = buf
            yield None


    def get_icon(self, name):
        theme = gtk.icon_theme_get_default()
        return theme.load_icon(name, 48, 0)


class NoDirException (StandardError):
    pass
