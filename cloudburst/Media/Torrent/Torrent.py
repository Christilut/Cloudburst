import threading
import time


class Torrent(object):

    # CONFIG VARS (can edit)
    # TODO base buffersize on bitrate and pieceSize
    padding_size = 3     # when this many pieces are left missing, the buffer is increased

    enable_debug_info = True

    def __init__(self, parent, torrenthandle, num_total_pieces, num_video_pieces, num_video_offset_pieces):

        self.parent = parent
        self.torrenthandle = torrenthandle
        self.num_total_pieces = num_total_pieces              # Total amount of pieces in the torrent
        self.num_video_pieces = num_video_pieces              # Total amount of pieces in the video file
        self.num_video_offset_pieces = num_video_offset_pieces    # Amount of pieces the video file is offset by. These pieces include all skipped files before the video

        # Init vars, do not edit
        self.torrent_status = None      # Status object of the torrent, obtained from libtorrent
        self.running = False            # if the torrent has been started # TODO
        self.seekpoint_piece = 0        # The piece that corresponds with the seekPoint
        self.current_piece = 0          # current piece the torrent should be downloading (+ bufferSize)
        self.seekpoint = 0              # from 0 to 1, point where the video wishes to play from
        self.header_available = False   # True if the header, footer and seekpoint are available
        self.pieces = {}                # Dict of the pieces that we are waiting for
        self.playable = False           # True if the file is playable

        # Some sanity checks
        assert self.buffer_size >= self.padding_size
        # TODO add more

        self.running = True

        # start thread that displays torrent info
        thread_torrent_info = threading.Thread(target=self.thread_torrent_info)
        thread_torrent_info.daemon = True
        thread_torrent_info.start()

        # Download is not started yet but torrent is active. This results in finding peers without downloading.

    def shutdown(self):
        self.running = False

    # Start the torrent. This will enable pieces and actually start the download.
    def start(self, seekpoint):

        # Seekpoint position
        self.seekpoint = seekpoint
        self.current_piece = int(float(self.num_video_pieces) / 1 * seekpoint) + self.num_video_offset_pieces
        self.seekpoint_piece = self.current_piece

        self.set_header_available(False)

        # Determine which pieces are wanted
        self.initialize_pieces()

    # Check which pieces already exist in an existing file, if available
    def check_cache(self):
        for n in iter(self.pieces):
            if self.torrenthandle.have_piece(n):
                if self.pieces[n]:
                    self.update_pieces(n)

    def set_playable(self, playable):
        self.playable = playable

    def get_bytes_downloaded(self):
        return self.torrent_status.total_wanted_done

    def get_bytes_wanted(self):
        return self.torrent_status.total_wanted

    def print_torrent_debug(self):

        infoSize = 55

        print 'Avail.\t(', self.current_piece, ')\t:',

        # Header
        if hasattr(self, 'headerSize') and self.headerSize != 0:
            for n in range(self.num_video_offset_pieces, self.num_video_offset_pieces + self.headerSize):
                if self.torrenthandle.have_piece(n):
                    print '1',
                else:
                    print '0',

            print '#',

        # Seekpoint
        for n in range(max(self.current_piece - infoSize, self.num_video_offset_pieces), min(self.current_piece + infoSize, self.num_video_pieces + self.num_video_offset_pieces - 1)):
            if self.torrenthandle.have_piece(n):
                print '1',
            else:
                print '0',

        # Footer
        if hasattr(self, 'footerSize') and self.footerSize != 0:
            print '#',
            for n in range(0, self.footerSize):
                if self.torrenthandle.have_piece(self.num_video_pieces + self.num_video_offset_pieces - 1 - n):
                    print '1',
                else:
                    print '0',

        print ''

        # Priorities
        print 'Prior.\t\t\t:',

        # Header
        if hasattr(self, 'headerSize') and self.headerSize != 0:
            for n in range(self.num_video_offset_pieces, self.num_video_offset_pieces + self.headerSize):
                if self.torrenthandle.piece_priority(n):
                    print '1',
                else:
                    print '0',

            print '#',

        # Seekpoint
        for n in range(max(self.current_piece - infoSize, self.num_video_offset_pieces), min(self.current_piece + infoSize, self.num_video_pieces + self.num_video_offset_pieces - 1)):
            if self.torrenthandle.piece_priority(n):
                print '1',
            else:
                print '0',

        # Footer
        if hasattr(self, 'footerSize') and self.footerSize != 0:
            print '#',
            for n in range(0, self.footerSize):
                if self.torrenthandle.piece_priority(self.num_video_pieces + self.num_video_offset_pieces - 1 - n):
                    print '1',
                else:
                    print '0',

        print ''

    # Sets the torrent to download the video data starting from the seekpoint
    def increase_buffer(self, piece_increase_amount):

        # Deadline in ms for normal pieces (not the missing ones)
        piece_deadline = 5000

        # Increase the buffer, this will be reflected in the priorities
        self.current_piece += piece_increase_amount

        # Create a new list of priorities, initially set to 0 (skip)
        piecelist = [0] * self.num_total_pieces

        # Clear the buffer piece list, this removes all the pieces (True and False) since they were all done
        self.pieces.clear()

        # Now handle the increase of the buffer
        for n in range(0, self.buffer_size):

            target_piece = self.current_piece + n

            if target_piece < self.num_video_pieces:    # dont go beyond the pieces of the video file
                piece = self.current_piece + n

                self.pieces[piece] = False  # Add to the list
                piecelist[piece] = 1    # Set priority
                self.torrenthandle.set_piece_deadline(piece, piece_deadline, 1)     # Set deadline and enable alert

        # Tell libtorrent to prioritize this list
        self.torrenthandle.prioritize_pieces(piecelist)

        # Return the list but use a copy otherwise a reference is used which will reflect changes in both ends
        return self.pieces.copy()

    # When header is in, call this function. Start to play movie and enable custom sequential download
    def set_header_available(self, available):
        self.header_available = available

        from cloudburst.media.player import Player
        Player.instance().set_header_available(available)

        if self.enable_debug_info:
            print 'Header available?', available
            self.print_torrent_debug()

    def update_pieces(self, piece_number): # TODO incorporate timer that sets deadlines and increases buffer
        if self.enable_debug_info:
            print 'Updated piece', piece_number

        if piece_number in self.pieces:
            if not self.pieces[piece_number]:
                self.pieces[piece_number] = True

        if not self.header_available:
            if self.check_header_available():
                self.set_header_available(True)

    def initialize_pieces(self):

        # Reset some vars incase of seeking
        self.parent.set_download_limit(False)
        self.header_increase_size_current = 0

        # Check cache once, in case the file already existed
        # self.checkCache() # TODO test this works

        # Clear header list incase of seeking an already playing video
        self.pieces.clear()

        # Header pieces
        for n in range(self.num_video_offset_pieces, self.num_video_offset_pieces + self.header_size):
            self.pieces[n] = False                # start of the file

        # Footer size (MKV Cueing data)
        if self.seekpoint_piece > self.num_video_offset_pieces:     # footer is only required for seeking # TODO make sure the footer does get downloaded when seeking after playing from 0
            for n in range(0, self.footer_size):
                self.pieces[self.num_video_pieces + self.num_video_offset_pieces - 1 - n] = False  # end of the file (MKV needs this)

        if self.enable_debug_info:
            print 'Seekpoint piece:', self.seekpoint_piece

        # Make sure the current piece cant go below the first piece of the video
        if self.current_piece < self.num_video_offset_pieces:
            self.current_piece = self.num_video_offset_pieces

    def thread_torrent_info(self):  # thread

        while not self.torrenthandle.is_seed() and self.running: # while not finished
            self.torrent_status = self.torrenthandle.status()

            # if self.torrentStatus.progress != 1: # if not finished
            state_str = ['queued', 'checking', 'downloading metadata',
                         'downloading', 'finished', 'seeding', 'allocating', 'checking fastresume']

            print '\rdown: %.1f kB/s, peers: %d, status: %s' % \
                (self.torrent_status.download_rate / 1000,
                 self.torrent_status.num_peers, state_str[self.torrent_status.state])

            if self.enable_debug_info:
                self.print_torrent_debug()

            time.sleep(3)