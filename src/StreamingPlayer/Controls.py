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
        # self.setMask(QPixmap('res/images/transparent.png').createHeuristicMask())

        self.initButtonPlayPause()
        self.initButtonStop()
        self.initSliderProgress()
        self.initSliderVolume()

        # take the parent widget size, after the controls are created
        self.resize(parent.size())

    def show(self):
        self.buttonPlayPause.show()
        self.buttonStop.show()
        self.sliderProgress.show()
        self.sliderVolume.show()

    def hide(self):
        self.buttonPlayPause.hide()
        self.buttonStop.hide()
        self.sliderProgress.hide()
        self.sliderVolume.hide()

    def resize(self, *__args):

        sliderHeight = 20
        sliderProgressOffset = 40

        sliderVolumeWidth = 100
        sliderVolumeWidthOffset = 60

        self.buttonPlayPause.resize(self.bigButtonSize, self.bigButtonSize)
        self.buttonPlayPause.move(self.bigButtonXoffset, self.parent.size().height() - (self.bigButtonSize + self.bigButtonYoffset))

        self.buttonStop.resize(self.bigButtonSize, self.bigButtonSize)
        self.buttonStop.move(self.parent.size().width() - self.bigButtonSize - self.bigButtonXoffset, self.parent.size().height() - (self.bigButtonSize + self.bigButtonYoffset))

        self.sliderProgress.resize(self.parent.size().width() - self.bigButtonXoffset * 2, sliderHeight)
        self.sliderProgress.move(self.bigButtonXoffset, self.parent.size().height() - sliderProgressOffset)

        self.sliderVolume.resize(sliderVolumeWidth, sliderHeight)
        self.sliderVolume.move(self.parent.size().width() / 2 - sliderVolumeWidth / 2, self.parent.size().height() - sliderVolumeWidthOffset)

    def initButtonPlayPause(self):
        self.buttonPlayPause = QPushButton('Play', self.parent)
        self.connect(self.buttonPlayPause, SIGNAL("clicked()"), self.parent.PlayPause)
        self.buttonPlayPause.show()

    def initButtonStop(self):
        self.buttonStop = QPushButton('Stop', self.parent)
        self.connect(self.buttonStop, SIGNAL("clicked()"), self.parent.Stop)
        self.buttonStop.show()

    def initSliderProgress(self):
        self.sliderProgress = QSlider(Qt.Horizontal, self.parent)
        self.sliderProgress.setMaximum(1000)
        self.connect(self.sliderProgress, SIGNAL("sliderMoved(int)"), self.parent.setPosition)

    def initSliderVolume(self):
        self.sliderVolume = QSlider(Qt.Horizontal, self.parent)
        self.sliderVolume.setMaximum(100)
        self.sliderVolume.setValue(100)
        self.connect(self.sliderVolume, SIGNAL("valueChanged(int)"), self.parent.setVolume)
        self.sliderVolume.show()


