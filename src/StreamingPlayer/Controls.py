from PyQt4.QtGui import *
from PyQt4.QtCore import *

class Controls(QWidget):

    bigButtonXoffset    = 15
    bigButtonYoffset    = 50
    bigButtonSize       = 50

    def __init__(self, parent):
        QWidget.__init__(self, parent)

        self.parent = parent

        # Transparency is a bitch, this creates a mask based on the png. This is a dirty hack.
        self.setMask(QPixmap('res/images/transparent.png').createHeuristicMask())

        self.initButtonPlayPause()
        self.initButtonStop()
        self.initSliderProgress()
        self.initSliderVolume()


    def initButtonPlayPause(self):
        self.buttonPlayPause = QPushButton('Play', self.parent)
        self.connect(self.buttonPlayPause, SIGNAL("clicked()"), self.parent.PlayPause)
        self.buttonPlayPause.show()

        self.buttonPlayPause.resize(self.bigButtonSize, self.bigButtonSize)
        self.buttonPlayPause.move(self.bigButtonXoffset, self.parent.size().height() - (self.bigButtonSize + self.bigButtonYoffset))


    def initButtonStop(self):
        self.buttonStop = QPushButton('Stop', self.parent)
        self.connect(self.buttonStop, SIGNAL("clicked()"), self.parent.Stop)
        self.buttonStop.show()

        self.buttonStop.resize(self.bigButtonSize, self.bigButtonSize)
        self.buttonStop.move(self.parent.size().width() - self.bigButtonSize - self.bigButtonXoffset, self.parent.size().height() - (self.bigButtonSize + self.bigButtonYoffset))

    def initSliderProgress(self):
        self.sliderProgress = QSlider(Qt.Horizontal, self.parent)
        self.sliderProgress.setMaximum(1000)
        self.connect(self.sliderProgress, SIGNAL("sliderMoved(int)"), self.parent.screen.setPosition)

        yOffset = 40

        self.sliderProgress.resize(self.parent.size().width() - self.bigButtonXoffset * 2, 20)
        self.sliderProgress.move(self.bigButtonXoffset, self.parent.size().height() - yOffset)

    def initSliderVolume(self):
        self.sliderVolume = QSlider(Qt.Horizontal, self.parent)
        self.sliderVolume.setMaximum(100)
        self.sliderVolume.setValue(100)
        self.connect(self.sliderVolume, SIGNAL("valueChanged(int)"), self.parent.setVolume)
        self.sliderVolume.show()

        width = 100
        yOffset = 60

        self.sliderVolume.resize(width, 20)
        self.sliderVolume.move(self.parent.size().width() / 2 - width / 2, self.parent.size().height() - yOffset)

