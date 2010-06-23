
import pyexiv2

class Metadata(pyexiv2.ImageMetadata):


    def get_content(self):
        content = ''

        if(self.comment):
            content = self.comment

        for tag in ['Exif.Image.ImageDescription',
                    'Iptc.Application2.Caption',
                    'Xmp.dc.description']:
            try:
                content = self[tag].value
            except KeyError:
                pass

        return content

