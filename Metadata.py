""" Inherits from pyexiv2.ImageMetadata and adds convenience functions

A list of available tag strings can be found at the following pages:

    http://exiv2.org/tags.html
    http://exiv2.org/iptc.html
    http://exiv2.org/tags-xmp-dc.html

"""

import pyexiv2

class Metadata(pyexiv2.ImageMetadata):

    def __init__(self,filename):
        self.filename = filename
        pyexiv2.ImageMetadata.__init__(self,filename)
        self.read()
        self.modified = False


    def conditional_write(self):
        """ write metadata only if internal modified flag is set """
        if(self.modified):
            self.write()
        return self.modified

    def get_content(self):
        """ Return the caption of the picture """
        return self.find_data(
            ['Iptc.Application2.Caption',
             'Exif.Photo.UserComment',
             'Exif.Image.XPComment',
             'Comment',
             'Exif.Image.ImageDescription',
             'Xmp.dc.description'])

    def set_content(self, value):
        """ Set the caption of the picture """
        if value != self.get_content():
            self.modified = True
            self.store_data(
                ['Iptc.Application2.Caption',
                 'Exif.Photo.UserComment',
                 'Exif.Image.XPComment',
                 'Comment',
                 'Exif.Image.ImageDescription'],
                value)

    def get_title(self):
        """ Return the title of the picture """

        return self.find_data(
            ['Iptc.Application2.Headline',
             'Iptc.Application2.ObjectName',
             'Exif.Image.XPTitle',
             'Xmp.dc.title'])

    def set_title(self, value):
        """ Set the title of the picture """
        if value != self.get_title():
            self.modified = True
            self.store_data(
                ['Iptc.Application2.Headline',
                 'Exif.Image.XPTitle'],
                value)

    def get_tags(self):
        """ Return tags of the picture as comma separated string"""
        return self.find_data(
            ['Iptc.Application2.Keywords',
             'Exif.Image.XPKeywords',
             'Exif.Category']);

    def set_tags(self, value):
        """ Set the given comma separated string of tags in the picture"""
        if value != self.get_tags():
            self.modified = True
            self.store_data(
                ['Iptc.Application2.Keywords',
                 'Exif.Image.XPKeywords'],
                value, True)


    def find_data(self, taglist):
        """ Go through the list of given tags until one containing a value
            is found, this value is then returned.
            Returns an empty string if no values could be found

        """
        value = ''
        for tag in taglist:
            try:
                if(tag.startswith('Iptc.')):
                    value = ", ".join(self[tag].values)
                elif (tag == 'Comment'):
                    value = self.comment
                else:
                    value = self[tag].value

                value = value.strip()
                if(value):
                    break
            except KeyError:
                pass

        try:
            value = unicode(value)
        except:
            #FIXME try to convert
            value = ''

        return value

    def store_data(self, taglist, value, ismulti=False):
        """ Store the given value in all given tags
            when ismulti is true, value is treated as a comma separated
            list and tried to be stored in a repeatable tag
        """
        for tag in taglist:
            if tag.startswith('Iptc.'):
                if(ismulti):
                    vlist = value.split(',')
                    vlist = map(str.strip,vlist)
                    self[tag] = pyexiv2.IptcTag(tag, vlist)
                else:
                    self[tag] = pyexiv2.IptcTag(tag, [value])
            elif tag.startswith('Exif.'):
                self[tag] = pyexiv2.ExifTag(tag, value)
            elif tag.startswith('Xmp.'):
                self[tag] = pyexiv2.XmpTag(tag, value)




