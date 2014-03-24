import sys

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4 import uic

from src.StreamingPlayer.StreamingPlayer import StreamingPlayer


# MainFrame is the container in which MainWidget resides, can also include statusbar, menubar, etc
class MainFrame(QMainWindow):
    def __init__(self):
        super(MainFrame, self).__init__()
        uic.loadUi('src/Interface/ui/mainframe.ui', self)
        self.setWindowTitle("Cloudburst")
        # self.setWindowFlags(Qt.FramelessWindowHint)
        self.setWindowIcon(QIcon('res/images/icon.png'))
        self.show()

        # Create the frame that holds the content, there must be one central widget
        self.mainWidget = MainWidget()
        self.setCentralWidget(self.mainWidget)

        # Adjust main window size to contents
        self.resize(self.mainWidget.size())

# MainWidget is the container that can hold layouts and is the only content of MainFrame. MainWidget contains all other UI content
class MainWidget(QWidget):
    def __init__(self):
        super(MainWidget, self).__init__()
        self.loadContent()
        self.setMinimumSize(QSize(640, 480))

    def loadContent(self):

        # Create a layout to put the TestContent in and add it to the main widget
        mainlayout = QStackedLayout()
        mainlayout.setContentsMargins(0, 0, 0, 0)


        # add more content here (be sure to add to a layout below)
        self.streamingPlayer = StreamingPlayer(self)
        mainlayout.addWidget(self.streamingPlayer)


        self.setLayout(mainlayout)
        self.resize(640, 480)


if __name__ == '__main__':

    # Initialize the application
    app = QApplication(sys.argv)

    # Create an empty main window
    mainframe = MainFrame()

    # Terminate program when exit button is pressed
    sys.exit(app.exec_())