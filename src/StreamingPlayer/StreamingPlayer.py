from PyQt4.QtGui import *
from PyQt4.QtCore import *
import ScreenVLC, Controls

class StreamingPlayer(QWidget):

    isPlaying = False
    updateTimerInterval = 100
    previousMousePos = None
    timeMouseNotMoving = 0
    showInterface = False

    def __init__(self, parent):
        QWidget.__init__(self, parent)

        self.resize(parent.size())

        # create the video player
        self.screen = ScreenVLC.ScreenVLC(self)

        # create overlay controls
        self.controls = Controls.Controls(self)

        # start timer to update the UI every updateTimerInterval ms
        self.updateTimer = QTimer(self)
        self.updateTimer.setInterval(self.updateTimerInterval)
        self.connect(self.updateTimer, SIGNAL("timeout()"), self.updateUI)

    def updateUI(self):
        # setting the slider to the desired position
        self.controls.sliderProgress.setValue(self.screen.mediaplayer.get_position() * 1000)
        # self.screen.mediaplayer.audio_set_volume(0)                                     # TEMP TO FORCE SOUND OFF FOR TESTING
        if not self.screen.mediaplayer.is_playing():
            self.Stop()

        # another nice hack here... since VLC consumes all mouse events, we cannot determine if the mouse is inside the video
        # but we can constantly ask VLC where the mouse is and figure it out ourselves
        mousePos = self.screen.mediaplayer.video_get_cursor(0)

        if mousePos == self.previousMousePos:
            self.timeMouseNotMoving += self.updateTimerInterval

            if self.timeMouseNotMoving >= 900 and self.showInterface:
                self.controls.hide()
                self.showInterface = False

        elif not self.showInterface:
            self.controls.show()
            self.showInterface = True
            self.timeMouseNotMoving = 0

        self.previousMousePos = mousePos

    def resizeEvent(self, event):
        self.screen.resize(self.size())
        self.controls.resize(self.size())

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

    def setPosition(self, position):
        self.screen.mediaplayer.set_position(position / 1000.0) # 1000 is for the precision
