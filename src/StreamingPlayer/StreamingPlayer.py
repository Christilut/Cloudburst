from PyQt4.QtGui import *
from PyQt4.QtCore import *
import ScreenVLC, Controls

class StreamingPlayer(QWidget):

    isPlaying = False

    def __init__(self, parent):
        QWidget.__init__(self, parent)

        self.resize(parent.size())

        self.screen = ScreenVLC.ScreenVLC(self)
        self.screen.show()


        # create overlay controls

        self.controls = Controls.Controls(self)
        self.controls.resize(self.size())
        self.controls.show()

        # start timer to update the UI every 200ms
        self.updateTimer = QTimer(self)
        self.updateTimer.setInterval(200) # 200ms
        self.connect(self.updateTimer, SIGNAL("timeout()"), self.updateUI)

    def updateUI(self):
        # setting the slider to the desired position
        self.controls.sliderProgress.setValue(self.screen.mediaplayer.get_position() * 1000)

        if not self.screen.mediaplayer.is_playing():
            self.Stop()

    def PlayPause(self):
        if self.isPlaying:
            self.screen.Pause()
            self.controls.buttonPlayPause.setText('Play')
            self.isPlaying = False
            self.updateTimer.stop()
        else:
            self.screen.Play()
            self.controls.buttonPlayPause.setText('Pause')
            self.isPlaying = True
            self.updateTimer.start()

    def Stop(self):
        self.screen.Stop()
        self.controls.buttonPlayPause.setText('Play')
        self.isPlaying = False
        self.updateTimer.stop()

    def setVolume(self, volume):
        self.screen.setVolume(volume)

