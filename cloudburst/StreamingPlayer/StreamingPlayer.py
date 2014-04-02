from PyQt4.QtGui import *
from PyQt4.QtCore import *
import ScreenVLC, Controls, Torrent
import os.path

class StreamingPlayer(QWidget):

    isPlaying = False # True if video file is being played
    updateTimerInterval = 100   # Time in ms between GUI updates
    bufferInterval = 500   # Time in ms between buffer checks
    previousMousePos = None # To keep track of the mouse, required to hide/show the GUI
    timeMouseNotMoving = 0  # To delay hiding of GUI
    showInterface = False   # True if GUI is being shown

    currentFilePath = ''    # Full path of current video file
    videoFileExists = False # True if video file is present on disk. Use this bool to prevent unnecessary disk access
    headerAvailable = False # True if header info of the video file is downloaded
    seekPointAvailable = False  # True if a buffer exists from the seek point onward
    desiredSeekPoint = 0

    lastMediaPosition = None # To determine if video is actually playing (based on media position difference)
    tryTorrentPlayInterval = 5000 # Time in ms between attempts to play the file while the header is being downloaded

    forwardBufferAvailable = False

    def __init__(self, parent):
        QWidget.__init__(self, parent)

        self.resize(parent.size())

        # create the video player
        self.screen = ScreenVLC.ScreenVLC(self)

        # create the torrent manager
        self.torrent = Torrent.Torrent(self)

        # create overlay controls
        self.controls = Controls.Controls(self)

        # start timer to update the UI every updateTimerInterval ms
        self.updateTimer = QTimer(self)
        self.updateTimer.setInterval(self.updateTimerInterval)
        self.connect(self.updateTimer, SIGNAL("timeout()"), self.updateUI)

        # TEMP test stuff below --------------------------------------------------------

        # TEMP open torrent
        self.seconds = 233
        self.SetDesiredSeekpoint(1 / (float(6132) / self.seconds))

        self.OpenTorrent('res/torrents/big_movie.torrent')




    def updateUI(self):
        # setting the slider to the desired position
        # self.controls.sliderProgress.setValue(self.screen.mediaplayer.get_position() * 1000) # TEMP disable auto update of progress slider
        # self.screen.mediaplayer.audio_set_volume(0)                                     # TEMP TO FORCE SOUND OFF FOR TESTING
        # if not self.screen.mediaplayer.is_playing():
        #     self.Stop() # TODO this is so when the video is over, UI gets reset but it caused issues

        # another nice hack here... since VLC consumes all mouse events, we cannot determine if the mouse is inside the video
        # but we can constantly ask VLC where the mouse is and figure it out ourselves
        mousePos = self.screen.mediaplayer.video_get_cursor(0)

        if mousePos == self.previousMousePos and QApplication.mouseButtons() == Qt.NoButton:
            self.timeMouseNotMoving += self.updateTimerInterval

            if self.timeMouseNotMoving >= 900 and self.showInterface:
                self.controls.hide()
                self.showInterface = False
                self.timeMouseNotMoving = 0

        elif self.timeMouseNotMoving == 0 and not self.showInterface: # this causes a 200ms delay, which is what we want
            self.controls.show()
            self.showInterface = True

        else:
            self.timeMouseNotMoving = 0

        self.previousMousePos = mousePos

    def resizeEvent(self, event):
        self.screen.resize(self.size())
        self.controls.resize(self.size())

    def HeaderAvailable(self, available):
        self.headerAvailable = available

    def SetDesiredSeekpoint(self, seekpoint): # from 0 to 1

        assert (seekpoint >= 0 and seekpoint < 1)
        print 'Seekpoint set to:', seekpoint
        self.desiredSeekPoint = seekpoint

    def OpenTorrent(self, path):
        if not self.currentFilePath == '':
            print 'File path already entered'
            return

        self.currentFilePath = self.torrent.StartTorrent(path, self.desiredSeekPoint)

        print 'Waiting for file: ' + self.currentFilePath

        self.BufferFile()

    def BufferFile(self):
        if not self.videoFileExists:
            if not os.path.isfile(self.currentFilePath):
                # print 'File does not yet exist, waiting 1 second...'
                pass
            else:
                print 'File found! Buffering...'
                self.videoFileExists = True

            QTimer.singleShot(self.bufferInterval, self.BufferFile)
            return
        else:
            #  Video file exists here, wait for buffers

            # Wait for the header
            if not self.headerAvailable:
                QTimer.singleShot(self.bufferInterval, self.BufferFile)
                return

            # Seekpoint data is available so we can start streaming, next data pieces are downloaded one by one from now on
            # At this point, buffer is large enough and the video should be playable
            self.OpenFile()
            self.TryTorrentFilePlay()

    def TryTorrentFilePlay(self):

        if self.lastMediaPosition == None:
            self.PlayAtSeekpoint()
            QTimer.singleShot(self.tryTorrentPlayInterval, self.TryTorrentFilePlay)

        elif self.lastMediaPosition == self.screen.mediaplayer.get_position() or self.screen.mediaplayer.get_position() == 0:

            # TODO try to use the fact that get_position() returns 0.0 when seeking fails
            self.screen.mediaplayer.stop()

            # Add a small delay because calling play instantly after stop may freeze python
            QTimer.singleShot(100, self.PlayAtSeekpoint)

            QTimer.singleShot(self.tryTorrentPlayInterval, self.TryTorrentFilePlay)

        else:
            self.isPlaying = True
            self.Pause()
            print 'Can succesfully play'

            QTimer.singleShot(1000, self.WaitForForwardBuffer)

        self.lastMediaPosition = self.screen.mediaplayer.get_position()

    def WaitForForwardBuffer(self):

        if self.forwardBufferAvailable:
            self.Play()
        else:
            QTimer.singleShot(100, self.WaitForForwardBuffer)


    def OpenFile(self):
        if self.currentFilePath == '':
            print 'No file selected'
            return

        self.screen.OpenFile(self.currentFilePath)
        print 'Opening file:', self.currentFilePath

    def PlayPause(self): # TODO current not used, isPlaying is ambiguous
        if self.isPlaying:
            self.Pause()
        else:
            self.Play()

    def PlayAtSeekpoint(self):
        self.screen.Play(self.desiredSeekPoint)
        self.controls.buttonPlayPause.setText('Pause')
        self.updateTimer.start()

    def Play(self):
        self.screen.Play()
        self.controls.buttonPlayPause.setText('Pause')
        self.updateTimer.start()

    def Pause(self):
        self.screen.Pause()
        self.controls.buttonPlayPause.setText('Play')
        self.updateTimer.stop()

    def Stop(self):
        self.screen.Stop()
        self.controls.buttonPlayPause.setText('Play')
        self.isPlaying = False
        self.updateTimer.stop()
        self.desiredSeekPoint = 0

    def SetVolume(self, volume):
        self.screen.setVolume(volume)

    def SetPosition(self):
        position = float(self.controls.sliderProgress.value()) / 1000

        self.screen.mediaplayer.set_position(position) # 1000 is for the precision
        print 'Seekpoint:', position * 100, '%'

