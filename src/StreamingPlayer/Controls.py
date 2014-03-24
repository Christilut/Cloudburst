from PyQt4.QtGui import *
from PyQt4.QtCore import *
import os
class Controls(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self)

        # Transparency is a bitch, this creates a mask based on the png. This is a dirty hack.
        # self.setMask(QPixmap('res/images/transparent.png').createHeuristicMask())

        # btn = QPushButton('tasef', parent)
        # btn.setAttribute(Qt.WA_NoSystemBackground)
        # btn.show()

        self.resize(parent.size())

        buttonPlayPause = ButtonPlayPause(self)
        buttonPlayPause.show()
        buttonPlayPause.move(parent.width() / 2 - buttonPlayPause.width() / 2,
                             parent.height() / 2 - buttonPlayPause.height() / 2)


class ButtonPlayPause(QLabel):
    IMAGE_PLAY = 'res/images/player_play.png'
    IMAGE_PAUSE = 'res/images/player_pause.png'

    def __init__(self,  parent):
        QPushButton.__init__(self, parent)

        self.pixmapPlay = QPixmap(self.IMAGE_PLAY)
        self.pixmapPause = QPixmap(self.IMAGE_PAUSE)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.drawPixmap(event.rect(), self.pixmapPlay)


    def sizeHint(self):
        return self.pixmapPlay.size() / 6 # TODO uniform scaling

    def mousePressEvent(self, QMouseEvent):
        self.emit(SIGNAL('clicked()'))

        print 'click'
