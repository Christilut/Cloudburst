from cloudburst.Media.Streamer import Streamer
from cloudburst.Media.TorrentManager import TorrentManager
from cloudburst.util.Singleton import Singleton

@Singleton
class MediaManager():

    def __init__(self):

        seekpoint = 0  # position in video from 0 to 1

        # Create the torrent manager
        self.torrentManager = TorrentManager.Instance()
        path = self.torrentManager.openTorrent('res/torrents/mp42.torrent')     # init torrent, get peers
        self.torrentManager.startTorrent(seekpoint=seekpoint)   # start the download

        # Start the streaming back end
        self.streamer = Streamer.Instance() # create it
        self.streamer.waitForFileBuffer(path, seekpoint)    # this starts playing when buffer available


    # To gracefully shutdown
    def shutdown(self):
        self.streamer.shutdown()
        self.torrentManager.shutdown()

    # Set the seek point of the video from 0 to 1, torrent will buffer from there and video will wait for the buffer
    def setVideoPosition(self, position):

        assert (position >= 0 and position < 1)

        if self.torrentManager.videoFileType == 'AVI':
            print '.avi files do not support seeking'
            return # abort seeking

        self.torrentManager.startTorrent(seekpoint=position)

        self.streamer.stop()
        self.streamer.waitForFileBuffer(seekpoint=position)

    # Returns true of false
    def isBuffering(self):
        pass

    # Returns estimated buffer progress from 0 to 1
    def getBufferProgress(self):
        pass

    # Returns speed of buffering in bytes/s
    def getBufferSpeed(self):
        pass

    # Returns a list of size 100 with 1's and 0's where 1 means the percentage of that part of the video is available
    def getVideoAvailability(self):
        pass