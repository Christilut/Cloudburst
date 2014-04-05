import Torrent
import os.path, threading
from threading import Timer

class StreamingPlayer(threading.Thread):

    isPlaying = False # True if video file is being played
    bufferInterval = 0.5   # Time in s between buffer checks
    previousMousePos = None # To keep track of the mouse, required to hide/show the GUI
    timeMouseNotMoving = 0  # To delay hiding of GUI
    showInterface = False   # True if GUI is being shown

    currentFilePath = ''    # Full path of current video file
    videoFileExists = False # True if video file is present on disk. Use this bool to prevent unnecessary disk access
    headerAvailable = False # True if header info of the video file is downloaded
    seekPointAvailable = False  # True if a buffer exists from the seek point onward
    desiredSeekPoint = 0

    lastMediaPosition = None # To determine if video is actually playing (based on media position difference)
    tryTorrentPlayInterval = 5 # Time in s between attempts to play the file while the header is being downloaded

    forwardBufferAvailable = False

    torrentPlayTimer = None
    bufferTimer = None
    waitForForwardBufferTimer = None

    def __init__(self, parent):
        self.parent = parent
        threading.Thread.__init__(self)

        # create the torrent manager
        self.torrent = Torrent.Torrent(self)

        # TEMP test stuff below --------------------------------------------------------

        # TEMP open torrent
        # self.seconds = 233
        # self.SetDesiredSeekpoint(1 / (float(6132) / self.seconds))

    def run(self):

        while not self.parent.isLoaded: # TEMP
            pass

        # self.parent.vlcInterface.loadVideo2()


    def Shutdown(self):

        if self.bufferTimer is not None:
            self.bufferTimer.cancel()

        if self.torrentPlayTimer is not None:
            self.torrentPlayTimer.cancel()

        if self.waitForForwardBufferTimer is not None:
            self.waitForForwardBufferTimer.cancel()

        self.torrent.Shutdown()


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

            self.bufferTimer = Timer(self.bufferInterval, self.BufferFile)
            self.bufferTimer.start()

            return
        else:
            #  Video file exists here, wait for buffers

            # Wait for the header
            if not self.headerAvailable:
                self.bufferTimer = Timer(self.bufferInterval, self.BufferFile)
                self.bufferTimer.start()
                return

            # Seekpoint data is available so we can start streaming, next data pieces are downloaded one by one from now on
            # At this point, buffer is large enough and the video should be playable
            # self.OpenFile()
            # self.TryTorrentFilePlay()

            # TEMP
            # VlcInterface.loadVideo()

    def TryTorrentFilePlay(self):

        if self.lastMediaPosition == None:
            self.PlayAtSeekpoint()
            self.torrentPlayTimer = Timer(self.tryTorrentPlayInterval, self.TryTorrentFilePlay)
            self.torrentPlayTimer.start()

        elif self.lastMediaPosition == self.screen.mediaplayer.get_position() or self.screen.mediaplayer.get_position() == 0:

            # TODO try to use the fact that get_position() returns 0.0 when seeking fails
            self.screen.mediaplayer.stop()

            # Add a small delay because calling play instantly after stop may freeze python
            Timer(0.1, self.PlayAtSeekpoint).start()

            self.torrentPlayTimer = Timer(self.tryTorrentPlayInterval, self.TryTorrentFilePlay)
            self.torrentPlayTimer.start()

        else:
            self.isPlaying = True
            self.Pause()
            print 'Can succesfully play'

            self.waitForForwardBufferTimer = Timer(1, self.WaitForForwardBuffer)
            self.waitForForwardBufferTimer.start()

        self.lastMediaPosition = self.screen.mediaplayer.get_position()

    def WaitForForwardBuffer(self):

        if self.forwardBufferAvailable:
            self.Play()
        else:
            self.waitForForwardBufferTimer = Timer(0.1, self.WaitForForwardBuffer)
            self.waitForForwardBufferTimer.start()


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

    def Play(self):
        self.screen.Play()
        self.controls.buttonPlayPause.setText('Pause')

    def Pause(self):
        self.screen.Pause()
        self.controls.buttonPlayPause.setText('Play')

    def Stop(self):
        self.screen.Stop()
        self.controls.buttonPlayPause.setText('Play')
        self.isPlaying = False
        self.desiredSeekPoint = 0

    def SetVolume(self, volume):
        self.screen.setVolume(volume)

    def SetPosition(self):
        position = float(self.controls.sliderProgress.value()) / 1000

        self.screen.mediaplayer.set_position(position) # 1000 is for the precision
        print 'Seekpoint:', position * 100, '%'

