import sys
import gtk
import re
import ConfigParser
import os

from FileManager import FileManager, NoDirException
from whoosh.support.pyparsing import ParseException
from Metadata import Metadata

LIBRARY = "test"


class PicThing:
    window   = None
    builder  = None
    iconview = None
    filemgr  = None
    meta     = None
    libs     = None

    def on_window_destroy(self, widget, data=None):
        gtk.main_quit()


    def __init__(self):
        self.builder = gtk.Builder()
        self.builder.add_from_file("picthing.glade")

        self.window = self.builder.get_object("window")
        self.builder.connect_signals(self)

        config = ConfigParser.ConfigParser()
        config.read(['picthing.ini', os.path.expanduser('~/.picthing.ini')])
        self.libs = config.items('libraries')

        place   = self.builder.get_object("place_librarypicker")
        libpick =  gtk.combo_box_new_text()
        libpick.connect('changed',self.action_switchlibrary)
        place.add(libpick)
        libpick.show()
        if(len(self.libs)):
            for lib in self.libs:
                libpick.append_text(lib[0])
            libpick.set_active(0)
        else:
            #FIXME use some dialog here
            sys.exit()



    def action_switchlibrary(self, widget):
        """ Load a new library """
        library = self.libs[widget.get_active()]
        print "loading library '"+library[0]+"' in '"+library[1]+"'"
        self.meta     = None
        self.builder.get_object('notebook').set_current_page(0)
        if(self.filemgr != None):
            self.filemgr.index.close();
        self.filemgr  = FileManager(library[1])
        self.iconview = self.builder.get_object("iconview")
        self.iconview.set_model(self.filemgr.store)
        self.iconview.set_text_column(self.filemgr.COL_TITLE)
        self.iconview.set_pixbuf_column(self.filemgr.COL_PIXBUF)
        self.iconview.set_tooltip_column(self.filemgr.COL_PATH)
        self.new_query('')


    def action_search(self,widget):
        querybox = self.builder.get_object("querybox")
        self.set_status("Searching...")

        query = querybox.get_text()
        query = query.strip()
        m = re.search('^folder:("([^"]*)")?$',query)

        try:
            if(m):
                query = m.group(2);
                self.filemgr.browse(query)
            elif(query == ''):
                self.filemgr.browse(query)
            else:
                    self.filemgr.search(query)

            self.set_status("okay")

        except ParseException:
            self.set_status("Couldn't parse query")
        except KeyError:
            self.set_status("Wrong field name")
        except NoDirException:
            self.set_status("No such directory")

        self.builder.get_object('notebook').set_current_page(0)


    def action_iconclick(self,widget,item):
        model = widget.get_model()
        path  = model[item][self.filemgr.COL_PATH]
        ftype = model[item][self.filemgr.COL_TYPE]

        if(ftype == 'dir'):
            if(path):
                self.new_query('folder:"'+path+'"')
            else:
                self.new_query('')
        else:
            self.builder.get_object('notebook').set_current_page(1)

    def action_pageswitch(self,notebook, page, page_num):
        """ Signal handler. Activates when the notebok tab is switched """
        if(page_num == 1):
            self.load_image()
        else:
            self.meta = None


    def action_imgnext(self, button):
        """ Navigate to the next image in icon view """
        pos = self.get_currentpos()
        pos = self.filemgr.get_nextimagepos(pos)
        if(pos != None):
            self.iconview.select_path(pos)
            self.load_image()


    def action_imgprev(self, button):
        """ Navigate to the previous image in icon view """
        pos = self.get_currentpos()
        pos = self.filemgr.get_previmagepos(pos)
        if(pos != None):
            self.iconview.select_path(pos)
            self.load_image()


    def get_currentpos(self):
        """ return the number (position) of the currently selected icon

            returns None if nothing is selected
        """
        pos = self.iconview.get_selected_items()

        if(pos == None):
            return None;
        return pos[0][0] # array, tuple


    def load_image(self):
        """ Load the next image to show """
        self.save_image()

        panel = self.builder.get_object('imagepanel')
        panel.hide()

        pos = self.get_currentpos()
        if(pos == None):
            return
        img = self.filemgr.get_itemat(pos)

        if(img['ft'] == 'dir'):
            return

        pixmap = self.builder.get_object('image')
        pixmap.set_from_file(img['fn'])

        self.meta = Metadata(img['fn']);
        self.builder.get_object('imgtitle').set_text(self.meta.get_title())
        self.builder.get_object('imgcontent').set_text(self.meta.get_content())
        self.builder.get_object('imgtags').set_text(self.meta.get_tags())
        panel.show()

    def save_image(self):
        """ Save metadata of the currently loaded image (if any) """
        if(self.meta == None):
            return
        cnt = self.builder.get_object('imgcontent');
        self.meta.set_title(   self.builder.get_object('imgtitle').get_text()   )
        self.meta.set_content( cnt.get_text(cnt.get_start_iter(),cnt.get_end_iter()) )
        self.meta.set_tags(    self.builder.get_object('imgtags').get_text()    )
        if self.meta.conditional_write():
            # update index with new data
            self.filemgr.index.update_image(self.meta.filename)


    def new_query(self,query):
        """ Set a new search or browse query and execute it """
        querybox = self.builder.get_object("querybox")
        querybox.set_text(query)
        self.action_search(None)


    def set_status(self,text,context=1):
        status = self.builder.get_object("statusbar")
        status.push(context,text)


if __name__ == "__main__":
    gtk.gdk.threads_init()
    editor = PicThing()
    editor.window.show()
    gtk.main()
