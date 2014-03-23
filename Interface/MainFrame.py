import sys

from PyQt4 import QtGui, uic, QtCore

from Interface.StreamingPlayer.StreamingPlayer import StreamingPlayer


# MainFrame is the container in which MainWidget resides, can also include statusbar, menubar, etc
class MainFrame(QtGui.QMainWindow):
    def __init__(self):
        super(MainFrame, self).__init__()
        uic.loadUi('ui/mainframe.ui', self)
        self.setWindowTitle("Cloudburst")
        # self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setWindowIcon(QtGui.QIcon('images/icon.png'))
        self.show()

        # Create the frame that holds the content, there must be one central widget
        mainwidget = MainWidget()
        self.setCentralWidget(mainwidget)

        # Adjust main window size to contents
        self.resize(mainwidget.size())

# MainWidget is the container that can hold layouts and is the only content of MainFrame. MainWidget contains all other UI content
class MainWidget(QtGui.QWidget):
    def __init__(self):
        super(MainWidget, self).__init__()
        self.loadContent()

    def loadContent(self):

        # Create a layout to put the TestContent in and add it to the main widget
        mainlayout = QtGui.QStackedLayout()
        mainlayout.setContentsMargins(0, 0, 0, 0)


        # add more content here (be sure to add to a layout below)
        streamingplayer = StreamingPlayer()
        mainlayout.addWidget(streamingplayer)


        self.setLayout(mainlayout)
        self.resize(640, 480)



if __name__ == '__main__':

    # Initialize the application
    app = QtGui.QApplication(sys.argv)

    # Create an empty main window
    mainframe = MainFrame()

    # Terminate program when exit button is pressed
    sys.exit(app.exec_())