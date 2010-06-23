""" Inherits from pyexiv2.ImageMetadata and adds convenience functions

A list of available tag strings can be found at the following pages:

    http://exiv2.org/tags.html
    http://exiv2.org/iptc.html
    http://exiv2.org/tags-xmp-dc.html

"""

import pyexiv2

class Metadata(pyexiv2.ImageMetadata):

    def __init__(self,filename):
        pyexiv2.ImageMetadata.__init__(self,filename)
        self.read()


    def get_content(self):
        """ Return the caption of the picture """
        return self.find_data(
            ['Iptc.Application2.Caption',
             'Exif.Photo.UserComment'
             'Exif.Image.XPComment',
             'Comment',
             'Exif.Image.ImageDescription',
             'Xmp.dc.description'])

    def get_title(self):
        """ Return the title of the picture """
        return self.find_data(
            ['Iptc.Application2.Headline',
             'Iptc.Application2.ObjectName',
             'Exif.Image.XPTitle',
             'Xmp.dc.title'])


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

