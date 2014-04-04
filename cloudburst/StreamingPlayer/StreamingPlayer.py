import Torrent
import os.path, threading, time
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

        self.isRunning = True

        # create the torrent manager
        self.torrent = Torrent.Torrent(self)

        # TEMP test stuff below --------------------------------------------------------

        # TEMP open torrent
        # self.seconds = 233
        # self.SetDesiredSeekpoint(1 / (float(6132) / self.seconds))

    def run(self):

        while not self.parent.isLoaded: # TEMP
            pass

        while self.isRunning:
            self.parent.vlcInterface.test()
            time.sleep(1)



    def shutdown(self):

        self.isRunning = False

        if self.bufferTimer is not None:
            self.bufferTimer.cancel()

        if self.torrentPlayTimer is not None:
            self.torrentPlayTimer.cancel()

        if self.waitForForwardBufferTimer is not None:
            self.waitForForwardBufferTimer.cancel()

        self.torrent.shutdown()


    def setHeaderAvailable(self, available):
        self.headerAvailable = available

    def setDesiredSeekpoint(self, seekpoint): # from 0 to 1

        assert (seekpoint >= 0 and seekpoint < 1)
        print 'Seekpoint set to:', seekpoint
        self.desiredSeekPoint = seekpoint

    def openTorrent(self, path):
        if not self.currentFilePath == '':
            print 'File path already entered'
            return

        self.currentFilePath = self.torrent.startTorrent(path, self.desiredSeekPoint)

        print 'Waiting for file: ' + self.currentFilePath

        self.waitForFileBuffer()

    def waitForFileBuffer(self):
        if not self.videoFileExists:
            if not os.path.isfile(self.currentFilePath):
                # print 'File does not yet exist, waiting 1 second...'
                pass
            else:
                print 'File found! Buffering...'
                self.videoFileExists = True

            self.bufferTimer = Timer(self.bufferInterval, self.waitForFileBuffer)
            self.bufferTimer.start()

            return
        else:
            #  Video file exists here, wait for buffers

            # Wait for the header
            if not self.headerAvailable:
                self.bufferTimer = Timer(self.bufferInterval, self.waitForFileBuffer)
                self.bufferTimer.start()
                return

            # Seekpoint data is available so we can start streaming, next data pieces are downloaded one by one from now on
            # At this point, buffer is large enough and the video should be playable
            self.openFile()
            self.tryTorrentFilePlay()

    def tryTorrentFilePlay(self):

        if self.lastMediaPosition == None:
            self.playAtSeekpoint()
            self.torrentPlayTimer = Timer(self.tryTorrentPlayInterval, self.tryTorrentFilePlay)
            self.torrentPlayTimer.start()

        elif self.lastMediaPosition == self.getPosition() or self.getPosition() == 0:

            # TODO try to use the fact that get_position() returns 0.0 when seeking fails
            self.stop()

            # Add a small delay because calling play instantly after stop may freeze python
            Timer(0.1, self.playAtSeekpoint).start()

            self.torrentPlayTimer = Timer(self.tryTorrentPlayInterval, self.tryTorrentFilePlay)
            self.torrentPlayTimer.start()

        else:
            self.isPlaying = True
            self.pause()
            print 'Can succesfully play'

            self.waitForForwardBufferTimer = Timer(1, self.waitForForwardBuffer)
            self.waitForForwardBufferTimer.start()

        self.lastMediaPosition = self.getPosition()
        print 'Called TryTorrent'

    def waitForForwardBuffer(self):

        if self.forwardBufferAvailable:
            self.play()
        else:
            self.waitForForwardBufferTimer = Timer(0.1, self.waitForForwardBuffer)
            self.waitForForwardBufferTimer.start()


    def openFile(self):
        if self.currentFilePath == '':
            print 'No file selected'
            return

        self.parent.vlcInterface.openFile(self.currentFilePath)
        print 'Opening file:', self.currentFilePath

    def playPause(self): # TODO current not used, isPlaying is ambiguous
        self.parent.vlcInterface.playPause()

    def playAtSeekpoint(self):
        self.play()
        self.parent.vlcInterface.setPosition(self.desiredSeekPoint)

    def play(self):
        self.parent.vlcInterface.play()

    def pause(self):
        self.parent.vlcInterface.pause()

    def stop(self):
        self.parent.vlcInterface.stop()
        self.isPlaying = False
        self.desiredSeekPoint = 0

    def setVolume(self, volume):
        pass

    def getPosition(self):
        return self.parent.vlcInterface.getPosition()

