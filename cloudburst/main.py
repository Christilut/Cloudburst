import sys

from PyQt4 import QtGui, uic
#import urllib
#from os import listdir, walk
#from os.path import isfile, join, splitext

#import xml.etree.ElementTree as ET


class Shows(QtGui.QMainWindow):
    def __init__(self):
        super(Shows, self).__init__()

        uic.loadUi('src/Interface/ui/show_overview.ui', self)

        print 'Blaat'
        #self.searchButton.clicked.connect(self.onSearchButtonClicked)
        #self.loadShowsButton.clicked.connect(self.onLoadShowsButtonClicked)

        self.show()

        #t = Tvdb()
        #print t['Scrubs'][1][24]['episodename']


def main():
    app = QtGui.QApplication(sys.argv)
    Shows()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()