from PyQt4 import QtGui
import Screen, Controls

class StreamingPlayer(QtGui.QWidget):
    def __init__(self):
        super(StreamingPlayer, self).__init__()

        # layout = QtGui.QHBoxLayout()
        # self.addChildWidget(Screen.Screen())
        # layout.addWidget(Controls.Controls())
        # screen = Screen.Screen()
        # screen.resize(400,400)
        # screen.show()


        # Remove margins
        # layout.setContentsMargins(0, 0, 0, 0)

        # self.setLayout(layout);