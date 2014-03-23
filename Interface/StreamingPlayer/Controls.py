from PyQt4 import QtGui, QtCore, Qt

class Controls(QtGui.QWidget):
    def __init__(self):
        super(Controls, self).__init__()

        # self.setPalette(Qt.)

        # btn = QtGui.QPushButton('test')
        # btn.show()



    def paintEvent(self, QPaintEvent):
        painter = QtGui.QPainter()
        painter.begin(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)


        painter.setPen(QtGui.QColor(255, 0, 0))
        painter.drawRect(100, 100, 100, 100)