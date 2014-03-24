from PyQt4.QtGui import *
from PyQt4.phonon import Phonon


class ScreenPhonon(Phonon.VideoWidget):
    def __init__(self, parent):
        Phonon.VideoWidget.__init__(self, parent)

        media_src = Phonon.MediaSource('D:\\temp\\test.mpg')

        media_obj = Phonon.MediaObject(self)
        media_obj.setCurrentSource(media_src)

        Phonon.createPath(media_obj, self)

        audio_out = Phonon.AudioOutput(Phonon.VideoCategory, self)
        Phonon.createPath(media_obj, audio_out)

        self.resize(parent.size())

        media_obj.play()


