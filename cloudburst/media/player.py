import os.path
from threading import Timer

from cloudburst.util.Singleton import Singleton
from cloudburst.vlc import VLC


@Singleton
class Player():

    # Vars, can be edited
    bufferInterval = 0.5                            # Time in s between buffer checks
    tryTorrentPlayInterval = 5                      # Time in s between attempts to play the file while the header is being downloaded

    def __init__(self):

        self.vlc = VLC.instance()                   # Get the singleton instance

        self.running = True

        # init vars, should not be edited
        self.play_timer = None                      # timer, VLC will attempt to play the file every time this is called
        self.buffer_timer = None                    # timer, time between checks if a) the file exists and b) the header is available
        self.forward_buffer_timer = None            # timer, tiem between checks if the forward buffer (only for MKV) is available
        self.forward_buffer_available = False       # True if MKV can start playing from a seekpoint
        self.video_file_exists = False              # True if video file is present on disk. Use this bool to prevent unnecessary disk access
        self.header_available = False               # True if header info of the video file is downloaded
        self.seekpoint_available = False            # True if a buffer exists from the seek point onward
        self.desired_seekpoint = 0                  # from 0 to 1, the point where the video wishes to play from
        self.previous_video_position = None         # To determine if video is actually playing (based on media position difference)
        self.video_path = None

    def shutdown(self):

        self.running = False

        # cancelling timers is not required if they are set to .daemon = True

    def get_video_length(self):
        return self.vlc.get_video_length()

    def set_header_available(self, available):
        self.header_available = available

    def await_file(self, path=None, seekpoint=None):

        if self.buffer_timer is not None:
            self.buffer_timer.cancel()

        if seekpoint is not None:
            self.desired_seekpoint = seekpoint

        if path is not None:
            self.video_path = path  # TODO file check should be in mediaManager or something

        if not self.video_file_exists:
            if not os.path.isfile(self.video_path):
                pass
            else:
                print 'File found! Buffering...'
                self.video_file_exists = True

            self.buffer_timer = Timer(self.bufferInterval, self.await_file)
            self.buffer_timer.daemon = True
            self.buffer_timer.start()

            return
        else:
            #  Video file exists here, wait for buffering
            if not self.header_available:
                self.buffer_timer = Timer(self.bufferInterval, self.await_file)
                self.buffer_timer.daemon = True
                self.buffer_timer.start()
                return

            # Seekpoint data is available so we can start streaming, next data pieces are downloaded one by one from now on
            # At this point, buffer is large enough and the video should be playable
            self.open_file()

            self.previous_video_position = None     # initial value for tryTorrentFilePlay, reset here incase of seeking
            self.await_video_playable()

    def await_video_playable(self):
        if self.play_timer is not None:
            self.play_timer.cancel()

        print 'trying to play...', self.previous_video_position

        current_video_position = self.get_video_time()
        print 'current pos:', current_video_position

        if self.previous_video_position is None:
            self.play_seekpoint()
            self.play_timer = Timer(self.tryTorrentPlayInterval, self.await_video_playable)
            self.play_timer.daemon = True
            self.play_timer.start()
            
        elif self.previous_video_position == current_video_position or current_video_position == 0:
            # TODO try to use the fact that get_position() returns 0.0 when seeking fails
            self.stop()

            # Add a small delay because calling play instantly after stop may freeze python # TODO check if this is still true in web vlc
            onetime_play_timer = Timer(0.1, self.play_seekpoint)
            onetime_play_timer.daemon = True
            onetime_play_timer.start()
            
            self.play_timer = Timer(self.tryTorrentPlayInterval, self.await_video_playable)
            self.play_timer.daemon = True
            self.play_timer.start()

        else:
            from cloudburst.media.torrent_manager import TorrentManager
            torrent_manager = TorrentManager.instance()
            torrent_manager.torrent.set_playable(True)
            print 'Can succesfully play'
            torrent_manager.torrent.update_pieces(torrent_manager.torrent.seekpoint_piece)

            if self.desired_seekpoint != 0 and torrent_manager.video_file_extension == 'MKV':
                self.pause()

                self.forward_buffer_timer = Timer(1, self.await_forward_buffer)
                self.forward_buffer_timer.daemon = True
                self.forward_buffer_timer.start()

        self.previous_video_position = current_video_position

    def await_forward_buffer(self):

        if self.forward_buffer_available:
            self.play_seekpoint()
        else:
            self.forward_buffer_timer = Timer(0.1, self.await_forward_buffer)
            self.forward_buffer_timer.daemon = True
            self.forward_buffer_timer.start()

    def open_file(self):
        if self.video_path is None:
            print 'No file selected'
            return

        self.vlc.open_file(self.video_path)
        print 'Opening file:', self.video_path

    def play_pause(self):
        self.vlc.play_pause()

    def play_seekpoint(self):
        print 'Playing at seekpoint:', self.desired_seekpoint
        self.play()
        self.vlc.set_position(self.desired_seekpoint)

    def play(self):
        print 'Playing'
        self.vlc.play()

    def pause(self):
        self.vlc.pause()

    def stop(self):
        self.vlc.stop()
        from cloudburst.media.torrent_manager import TorrentManager
        torrent_mananger = TorrentManager.instance()
        torrent_mananger.torrent.set_playable(False)
        # self.desiredSeekPoint = 0

    def set_volume(self, volume):
        pass

    def get_video_position(self):
        return self.vlc.get_video_position()

    def get_video_time(self):
        return self.vlc.get_video_current_time()

