from PyQt4.QtGui import *
import ScreenVLC, Controls

class StreamingPlayer(QWidget):
    def __init__(self, parent):
        # super(StreamingPlayer, self).__init__()
        QWidget.__init__(self, parent)

        self.resize(parent.size())


        # screen = ScreenVLC.ScreenVLC(self)
        # screen.show()

        controls = Controls.Controls(self)
        controls.show()

