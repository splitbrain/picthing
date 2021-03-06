import sys
import gtk
import re
import ConfigParser
import os
import gobject
import urllib

from FileManager import FileManager, NoDirException
from whoosh.support.pyparsing import ParseException
from Metadata import Metadata
from ResizableImage import ResizableImage


class PicThing:
    window   = None
    builder  = None
    iconview = None
    filemgr  = None
    meta     = None
    libs     = None
    image    = None

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


        # add image canvas
        self.image = ResizableImage()
        self.image.show()
        self.builder.get_object("picframe").add(self.image)

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

        self.filemgr.index.tagcloud()


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

        self.meta = None
        if(page_num == 1):
            self.load_image()
        elif(page_num == 2):
            self.builder.get_object('tagcloud').set_markup(self.filemgr.get_tagcloudstring())



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

    def action_activate_link(self, widget, link):
        """ handle clicks in label links """
        link = urllib.unquote(link)
        self.new_query(link)

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
        self.image.hide()

        pos = self.get_currentpos()
        if(pos == None):
            return
        img = self.filemgr.get_itemat(pos)

        if(img['ft'] == 'dir'):
            return

        self.meta = Metadata(img['fn']);

        obj = self.builder.get_object('imgtitle')
        obj.set_text(self.meta.get_title())
        obj.set_sensitive(self.meta.writable)

        obj = self.builder.get_object('imgcontent')
        obj.set_text(self.meta.get_content())
        obj = self.builder.get_object('imgcontentbox')
        obj.set_sensitive(self.meta.writable)

        obj = self.builder.get_object('imgtags')
        obj.set_text(self.meta.get_tags())
        obj.set_sensitive(self.meta.writable)

        obj = self.builder.get_object('imgname')
        obj.set_text(os.path.basename(img['fn']))

        panel.show()

        while gtk.events_pending():
            gtk.main_iteration(False)
        self.image.set_from_file(img['fn'])
        self.image.show()

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



    def action_scandialog(self,widget):

        query = self.builder.get_object("querybox").get_text()
        m = re.search('folder:("([^"]*)")?$',query)

        if(m):
            base = m.group(2)
            base = os.path.join(self.filemgr.root,base)
        else:
            base = self.filemgr.root
        self.builder.get_object("scandialog_folder").set_text(base);


        prg = self.builder.get_object("scandialog_progress")
        prg.hide()
        prg.set_pulse_step(0.01)
        btn = self.builder.get_object("scandialog_execute")
        btn.set_sensitive(True)

        dialog = self.builder.get_object("scandialog")
        dialog.run()

    def action_scandialog_response(self,dialog,response_id):
        print response_id
        if response_id < 0:
            dialog.hide()
            # abort any running scan:
            self.filemgr.index.scan_stop()
            return

        prg = self.builder.get_object("scandialog_progress")
        prg.set_text('')
        prg.show()
        btn = self.builder.get_object("scandialog_execute")
        btn.set_sensitive(False)

        base = self.builder.get_object("scandialog_folder").get_text();

        self.filemgr.index.scan_start()
        scan = self.filemgr.index.scan_iterator(base,
                                                self.action_scan_loop,
                                                self.action_scan_exit)
        gobject.idle_add(scan.next)

    def action_scan_loop(self,fn,isimg):
        prg = self.builder.get_object("scandialog_progress")
        prg.show()
        prg.pulse()
        if isimg:
            prg.set_text(os.path.basename(fn))

    def action_scan_exit(self,isabort):
        dialog = self.builder.get_object("scandialog")
        dialog.hide()

if __name__ == "__main__":
    gtk.gdk.threads_init()
    editor = PicThing()
    editor.window.show()
    gtk.main()
