
import os
import gtk
import re

from Indexer import Indexer;



class FileManager:
    COL_TITLE  = 0
    COL_PATH   = 1
    COL_PIXBUF = 2
    COL_TYPE   = 3

    store = None
    root  = None
    index = None

    def __init__(self,root):
        self.store = gtk.ListStore(str, str, gtk.gdk.Pixbuf, str)
        self.root  = root
        self.index = Indexer(self.root)

    def search(self,query):
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

    def browse(self,folder):
        folder = folder.replace('..','')
        self.store.clear()

        print "browse "+folder;

        full = os.path.join(self.root,folder)
        full = os.path.abspath(full)
        imgre = re.compile('\.jpe?g$',re.IGNORECASE)

        if(not os.path.isdir(full)):
            return

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


    def get_icon(self, name):
        theme = gtk.icon_theme_get_default()
        return theme.load_icon(name, 48, 0)

