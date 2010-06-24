
import os
import gtk

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
        self.store = gtk.ListStore(str, str, gtk.gdk.Pixbuf, int)
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
                2])

    def get_icon(self, name):
        theme = gtk.icon_theme_get_default()
        return theme.load_icon(name, 48, 0)

