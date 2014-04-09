from cloudburst.media.player import Player
from cloudburst.media.torrent_manager import TorrentManager
from cloudburst.util.Singleton import Singleton

@Singleton
class MediaManager():

    def __init__(self):

        seekpoint = 0  # position in video from 0 to 1

        # Create the torrent manager
        self.torrent_manager = TorrentManager.instance()
        path = self.torrent_manager.open_torrent('res/torrents/avi.torrent')     # init torrent, get peers
        self.torrent_manager.start_torrent(seekpoint=seekpoint)   # start the download

        # Start the streaming back end
        self.streamer = Player.instance()             # create it
        self.streamer.await_file(path, seekpoint)       # this starts playing when buffer available

    # To gracefully shutdown
    def shutdown(self):
        self.streamer.shutdown()
        self.torrent_manager.shutdown()

    # Set the seek point of the video from 0 to 1, torrent will buffer from there and video will wait for the buffer
    def set_video_position(self, position):

        assert 0 <= position < 1

        if self.torrent_manager.video_file_extension == 'AVI':
            print '.avi files do not support seeking'
            return  # abort seeking

        self.torrent_manager.start_torrent(seekpoint=position)

        self.streamer.stop()
        self.streamer.await_file(seekpoint=position)

    # Returns true of false
    def is_buffering(self):
        pass

    # Returns estimated buffer progress from 0 to 1
    def buffer_progress(self):
        pass

    # Returns speed of buffering in bytes/s
    def buffer_speed(self):
        pass

    # Returns a list of size 100 with 1's and 0's where 1 means the percentage of that part of the video is available
    def video_availability(self):
        pass