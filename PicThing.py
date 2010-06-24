import sys
import gtk
import re

from FileManager import FileManager;


LIBRARY = "test"


class PicThing:
    window   = None
    builder  = None
    iconview = None
    filemgr  = None


    def on_window_destroy(self, widget, data=None):
        gtk.main_quit()


    def __init__(self):
        self.builder = gtk.Builder()
        self.builder.add_from_file("picthing.glade")

        self.window = self.builder.get_object("window")
        self.builder.connect_signals(self)

        self.filemgr = FileManager(LIBRARY)

        self.iconview = self.builder.get_object("iconview")
        self.iconview.set_model(self.filemgr.store)
        self.iconview.set_text_column(self.filemgr.COL_TITLE)
        self.iconview.set_pixbuf_column(self.filemgr.COL_PIXBUF)
        self.iconview.set_tooltip_column(self.filemgr.COL_PATH)



    def action_search(self,widget):
        self.set_status("Searching...")
        querybox = self.builder.get_object("querybox")
        query = querybox.get_text()
        query = query.strip()

        m = re.search('^folder:("([^"]*)")?$',query)
        if(m):
            query = m.group(2);
            self.filemgr.browse(query)
        elif(query == ''):
            self.filemgr.browse(query)
        else:
            self.filemgr.search(query)

        self.set_status("search done")


    def action_iconclick(self,widget,item):
        model = widget.get_model()
        path  = model[item][self.filemgr.COL_PATH]
        ftype = model[item][self.filemgr.COL_TYPE]

        if(ftype == 'dir'):
            if(path):
                self.new_query('folder:"'+path+'"')
            else:
                self.new_query('')

    def new_query(self,query):
        querybox = self.builder.get_object("querybox")
        querybox.set_text(query)
        self.action_search(None)


    def set_status(self,text,context=1):
        status = self.builder.get_object("statusbar")
        status.push(context,text)


if __name__ == "__main__":
    editor = PicThing()
    editor.window.show()
    gtk.main()
