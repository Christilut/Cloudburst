from PyQt4.QtGui import *
from PyQt4.QtCore import *
import ScreenVLC, Controls, Torrent
import os.path, time

class StreamingPlayer(QWidget):

    isPlaying = False # True if video file is being played
    updateTimerInterval = 100   # Time in ms between GUI updates
    bufferInterval = 1000   # Time in ms between buffer checks
    previousMousePos = None # To keep track of the mouse, required to hide/show the GUI
    timeMouseNotMoving = 0  # To delay hiding of GUI
    showInterface = False   # True if GUI is being shown

    currentFilePath = ''    # Full path of current video file
    videoFileExists = False # True if video file is present on disk. Use this bool to prevent unnecessary disk access
    headerAvailable = False # True if header info of the video file is downloaded
    seekPointAvailable = False  # True if a buffer exists from the seek point onward
    desiredSeekPoint = 0

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

        # TEMP REMOVE DOWNLOADED TORRENT
        import shutil
        shutil.rmtree('D:\\temp\\torrent', ignore_errors=True)

        # TEMP open torrent
        self.OpenTorrent('res/torrents/big_movie.torrent')

    #     # TEMP run checkTorrent every second
    #     self.checkTorrentTimer = QTimer(self)
    #     self.checkTorrentTimer.setInterval(100)
    #     self.connect(self.checkTorrentTimer, SIGNAL('timeout()'), self.checkTorrent)
    #     self.checkTorrentTimer.start()
    #
    # # TEMP method to check status of torrent
    # def checkTorrent(self):
    #     if self.torrent.torrentHandle.have_piece(0) and self.torrent.torrentHandle.have_piece(1677):
    #         print 'READY'

    def updateUI(self):
        # setting the slider to the desired position
        # self.controls.sliderProgress.setValue(self.screen.mediaplayer.get_position() * 1000) # TEMP disable auto update of progress slider
        self.screen.mediaplayer.audio_set_volume(0)                                     # TEMP TO FORCE SOUND OFF FOR TESTING
        if not self.screen.mediaplayer.is_playing():
            self.Stop()

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
        self.desiredSeekPoint = seekpoint

    def OpenTorrent(self, path):
        if not self.currentFilePath == '':
            print 'File path already entered'
            return

        self.currentFilePath = 'D:\\temp\\torrent\\' + self.torrent.StartTorrent(path)
        # self.currentFilePath = 'D:\\temp\\torrent\\Frozen.2013.FRENCH.720p.BluRay.x264-ROUGH\\Frozen.2013.FRENCH.720p.BluRay.x264-ROUGH.mkv' # TEMP

        print 'Opening file: ' + self.currentFilePath

        QTimer.singleShot(self.bufferInterval, self.BufferFile)

    def BufferFile(self):
        if not self.videoFileExists:
            if not os.path.isfile(self.currentFilePath):
                # print 'File does not yet exist, waiting 1 second...'
                pass
            else:
                print 'File exists! Buffering...'
                self.videoFileExists = True

            QTimer.singleShot(self.bufferInterval, self.BufferFile)
            return
        else:
            #  Video file exists here, wait for buffers

            # Wait for the header
            if not self.headerAvailable:
                print 'Waiting for video header...'
                QTimer.singleShot(self.bufferInterval, self.BufferFile)
                return

            # if not self.seekPointAvailable:
            #     print 'Waiting for seekpoint buffer...'
            #     QTimer.singleShot(self.bufferInterval, self.BufferFile)
            #     return

            # Seekpoint data is available so we can start streaming, next data pieces are downloaded one by one from now on

            # At this point, buffer is large enough and the video should be playable
            self.OpenFile()

    def OpenFile(self):
        if self.currentFilePath == '':
            print 'No file selected'
            return

        self.screen.OpenFile(self.currentFilePath)

        self.Play()

    def PlayPause(self):
        if self.isPlaying:
            self.Pause()
        else:
            self.Play()

    def Play(self):
        self.screen.Play(self.desiredSeekPoint)
        self.controls.buttonPlayPause.setText('Pause')
        self.isPlaying = True
        self.updateTimer.start()

    def Pause(self):
        self.screen.Pause()
        self.controls.buttonPlayPause.setText('Play')
        self.isPlaying = False
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
        position = self.controls.sliderProgress.value()
        self.screen.mediaplayer.set_position(position / 1000.0) # 1000 is for the precision
        print 'Seekpoint:', float(position) / 10, '%'
