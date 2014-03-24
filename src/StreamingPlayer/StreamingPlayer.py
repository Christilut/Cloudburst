from PyQt4.QtGui import *
import ScreenPhonon, Controls
from PyQt4.phonon import *
from PyQt4.QtOpenGL import *

class StreamingPlayer(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self, parent)

        self.resize(parent.size())

        screen = ScreenPhonon.ScreenPhonon(self)
        screen.show()


        # create overlay controls

        # controls = Controls.Controls(screen)
        # controls.show()


