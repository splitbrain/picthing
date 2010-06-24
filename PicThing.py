import sys
import gtk

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
        self.filemgr.search(querybox.get_text())
        self.set_status("search done")


    def set_status(self,text,context=1):
        status = self.builder.get_object("statusbar")
        status.push(context,text)


if __name__ == "__main__":
    editor = PicThing()
    editor.window.show()
    gtk.main()
