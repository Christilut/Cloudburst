import threading
import libtorrent as lt
import appdirs

from singleton.singleton import Singleton
from cloudburst.media.torrent.torrent_mkv import TorrentMKV
from cloudburst.media.torrent.torrent_mp4 import TorrentMP4
from cloudburst.media.torrent.torrent_avi import TorrentAVI

from cloudburst.config import Config
@Singleton
class TorrentManager():

    DEFAULT_DOWN_RATE = 2 * 1024 * 1024     # If required bitrate cant be calculated, default to this download limit in bytes

    torrent = None
    torrenthandle = None
    torrent_session = None

    video_file = lt.file_entry()

    def __init__(self):

        self.header_available = False
        self.num_total_pieces = 0
        self.num_video_offset_pieces = 0
        self.num_video_pieces = 0
        self.video_file_extension = None
        self.download_speed_limited = False

        if lt.version != '0.16.16.0':
            print 'Wrong version of libtorrent detected, please install version 0.16.16.0, you have', lt.version
            import sys
            sys.exit(-1)

        self.download_directory = appdirs.dirs.user_cache_dir + '\\Download\\'

        # TODO do not remove downloaded torrent but check it instead
        import shutil
        shutil.rmtree(self.download_directory, ignore_errors=True)

        self.running = True

        from cloudburst.media.player import Player
        self.streamer = Player.instance()

    def shutdown(self):
        self.running = False

        if self.torrent is not None:
            self.torrent.shutdown()

    def _disk_space_check(self):     # TODO
        pass

    def start_torrent(self, seekpoint=0):
        self.torrent.start(seekpoint)

    def open_torrent(self, path):

        if self.torrenthandle is not None:
            print 'Another torrent is already in progress'
            return

        self.torrent_session = lt.session()
        self.torrent_session.listen_on(6881, 6891)

        # Allocation settings (these should be default but make sure they are correct)
        settings = lt.session_settings()
        settings.close_redundant_connections = False    # This keeps peers connected
        settings.disk_io_write_mode = lt.io_buffer_mode_t.enable_os_cache
        settings.disk_io_read_mode = lt.io_buffer_mode_t.enable_os_cache

        self.torrent_session.set_settings(settings)

        e = lt.bdecode(open(path, 'rb').read())
        torrentinfo = lt.torrent_info(e)

        self.torrenthandle = self.torrent_session.add_torrent({'ti': torrentinfo, 'save_path': self.download_directory, 'storage_mode': lt.storage_mode_t.storage_mode_sparse})

        self.video_file = self._find_video_file(torrentinfo.files())

        # Disable all files, we do not want to download yet. Download starts when torrent.startTorrent() is called
        # for n in range(0, torrentInfo.num_files()):
        num_files_skipped = [0] * torrentinfo.num_files()
        self.torrenthandle.prioritize_files(num_files_skipped)

        # Print some torrent stats
        print 'Torrent piece size:', torrentinfo.piece_size(0) / 1024, 'kB'
        print 'Torrent total pieces:', torrentinfo.num_pieces()
        print 'Torrent total files:', torrentinfo.num_files()
        print 'Video file offset pieces:', self.num_video_offset_pieces

        self.num_total_pieces = torrentinfo.num_pieces()

        self._create_torrent()

        # start alert thread
        thread_alert = threading.Thread(target=self._thread_alert)
        thread_alert.daemon = True
        thread_alert.start()

        return self.download_directory + self.video_file.path

    # Instantiates the torrent object
    def _create_torrent(self):
        if self.video_file_extension == 'MKV':
            self.torrent = TorrentMKV(self, self.torrenthandle, self.num_total_pieces, self.num_video_pieces, self.num_video_offset_pieces)
        elif self.video_file_extension == 'MP4':
            self.torrent = TorrentMP4(self, self.torrenthandle, self.num_total_pieces, self.num_video_pieces, self.num_video_offset_pieces)
        elif self.video_file_extension == 'AVI':
            self.torrent = TorrentAVI(self, self.torrenthandle, self.num_total_pieces, self.num_video_pieces, self.num_video_offset_pieces)

    # Determine which file in the torrent is the video file. Currently based on size and is checked for extension.
    def _find_video_file(self, filelist):
        video_file = lt.file_entry()
        video_file_index = None

        # Currently it is presumed the largest file is the video file. This should be true most of the time.
        for n in range(0, len(filelist)):

            if filelist[n].size > video_file.size:
                video_file = filelist[n]
                video_file_index = n

        for n in range(0, len(filelist)):
            if not n == video_file_index:   # dont skip the video file
                self.torrenthandle.file_priority(n, 0)

        piece_priorities = self.torrenthandle.piece_priorities()

        # Count how many pieces are set to 0, these are all the skipped files
        self.num_video_offset_pieces = 0
        for n in range(0, len(piece_priorities)):
            if piece_priorities[n] == 0:
                self.num_video_offset_pieces += 1
            else:
                break

        # Now determine how many pieces are in the video file. This is the total amount of pieces in the torrent miuns the pieces of the files before and after the video file
        self.num_video_pieces = 0
        for n in range(self.num_video_offset_pieces, len(piece_priorities)):
            if piece_priorities[n] == 1:
                self.num_video_pieces += 1
            else:
                break

        # Additional check, make sure the file we want (video file) has one of these extensions: .mkv, .avi, .mp4
        split_string = str.split(video_file.path, '.')
        extension = split_string[len(split_string) - 1]

        if not (extension == 'mkv' or extension == 'avi' or extension == 'mp4'):
            print 'Video file has invalid file extension:', extension
            import sys
            sys.exit(-1)    # TODO better way to exit, this doesnt work with CEF

        self.video_file_extension = extension.upper()

        print 'Torrent configured for file type:', self.video_file_extension

        return video_file

    # Enable the download limit # TODO base it on bitrate
    def set_download_limit(self, limited):
        # Set download speed limit (apparently needs to be set after the torrent adding)
        self.download_speed_limited = limited

        if limited:

            video_file_size = float(self.video_file.size)       # in bytes
            video_file_length = float(self.streamer.get_video_length()) / 1000  # in s

            if video_file_length > 0:   # VLC may report -1 or 0 if it cant find the file length (seems to happen on AVI's)

                speed = video_file_size / video_file_length

                # add speed to be sure
                speed *= 1.5

            else:   # incase of no known length, set it to a default of 2MBps
                speed = self.DEFAULT_DOWN_RATE

            self.torrent_session.set_download_rate_limit(int(speed))
            print 'Download speed limit set to:', int(speed) / 1024, 'kB/s'

        else:
            print 'Disabled speed limit'
            self.torrent_session.set_download_rate_limit(-1)

    def _thread_alert(self):    # Thread. Checks torrent alert messages (like piece ready) and processes them
        text_piece = 'piece successful'     # Libtorrent always reports this when a piece is succesful, with an int attached

        while not self.torrenthandle.is_seed() and self.running:
            if self.torrent_session.wait_for_alert(10) is not None:     # None means no alert, 10ms timeout
                alert = str(self.torrent_session.pop_alert())

                if text_piece in alert:     # So we extract the int from the text
                    alert_substring = alert.find(text_piece)
                    piecenumber = int(alert[alert_substring + len(text_piece):])

                    # And pass it on to the method that checks pieces
                    self.torrent.update_pieces(piecenumber)   # TODO fix alert spam (has to do with setting deadline on pieces that are already in)

                # print alert # Uncomment this to see all alerts