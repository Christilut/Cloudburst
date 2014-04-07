from TorrentManager import TorrentManager
import os.path, threading, time
from threading import Timer

class StreamingPlayer():

    canPlay = False # True if video file is being played
    bufferInterval = 0.5   # Time in s between buffer checks

    currentFilePath = None    # Full path of current video file
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

        self.isRunning = True

        # create the torrent manager
        self.torrentManager = TorrentManager(self)

        # TEMP test stuff below --------------------------------------------------------

        # TEMP open torrent
        # self.setDesiredSeekpoint(0.4)

    def shutdown(self):

        self.isRunning = False

        if self.bufferTimer is not None:
            self.bufferTimer.cancel()

        if self.torrentPlayTimer is not None:
            self.torrentPlayTimer.cancel()

        if self.waitForForwardBufferTimer is not None:
            self.waitForForwardBufferTimer.cancel()

        self.torrentManager.shutdown()

    def getVideoLength(self):
        return self.parent.vlcInterface.getVideoLength()

    def setHeaderAvailable(self, available):
        self.headerAvailable = available

    def setDesiredSeekpoint(self, seekpoint): # from 0 to 1

        assert (seekpoint >= 0 and seekpoint < 1)

        if self.torrentManager.videoFileType == 'AVI':
            print '.avi files do not support seeking'
            return # abort seeking

        self.desiredSeekPoint = seekpoint

        if self.currentFilePath is not None:
            self.stop() # TODO perhaps delete torrent object and start a new one when seeking?
            self.torrentManager.torrent.setVideoPosition(seekpoint)
            self.waitForFileBuffer()

    def openTorrent(self, path):
        if self.currentFilePath is not None:
            print 'File path already entered'
            return

        self.currentFilePath = self.torrentManager.openTorrent(path, self.desiredSeekPoint)

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

            self.lastMediaPosition = None # initial value for tryTorrentFilePlay, reset here incase of seeking
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
            self.canPlay = True
            print 'Can succesfully play'
            self.torrentManager.torrent.updatePieceList(self.torrentManager.torrent.seekPointPieceNumber)

            if self.desiredSeekPoint != 0 and self.torrentManager.videoFileType == 'MKV':
                self.pause()

                self.waitForForwardBufferTimer = Timer(1, self.waitForForwardBuffer)
                self.waitForForwardBufferTimer.start()

        self.lastMediaPosition = self.getPosition()

    def waitForForwardBuffer(self):

        if self.forwardBufferAvailable:
            self.playAtSeekpoint()
        else:
            self.waitForForwardBufferTimer = Timer(0.1, self.waitForForwardBuffer)
            self.waitForForwardBufferTimer.start()


    def openFile(self):
        if self.currentFilePath is None:
            print 'No file selected'
            return

        self.parent.vlcInterface.openFile(self.currentFilePath)
        print 'Opening file:', self.currentFilePath

    def playPause(self):
        self.parent.vlcInterface.playPause()

    def playAtSeekpoint(self):
        print 'Playing at seekpoint:', self.desiredSeekPoint
        self.play()
        self.parent.vlcInterface.setPosition(self.desiredSeekPoint)

    def play(self):
        print 'Playing'
        self.parent.vlcInterface.play()

    def pause(self):
        self.parent.vlcInterface.pause()

    def stop(self):
        self.parent.vlcInterface.stop()
        self.canPlay = False
        # self.desiredSeekPoint = 0

    def setVolume(self, volume):
        pass

    def getPosition(self):
        return self.parent.vlcInterface.getPosition()

