import torrent


class TorrentMKV(torrent.Torrent):      # inherit from Torrent
    # VARS (can edit)

    buffer_size = 5  # in pieces, should be a minimum of paddingSize. Since the peers are lost when the header is available, \
                    #  the buffer needs to be big enough to re-initialize the torrent (around 10 should do) (based on bitrate)

    header_size = 1  # size of the header (first x pieces)
    footer_size = 1  # size of the footer (last x pieces)

    header_increase_size_amount = 2     # this many pieces are added to the front AND the back of the header buffer
    header_increase_offset = 1          # if this many pieces are missing from the header, headerIncreaseSizeAmount amount are added. Must be higher than headerIncreaseSizeAmount

    def __init__(self, parent, torrenthandle, num_total_pieces, num_video_pieces, num_video_offset_pieces):

        super(TorrentMKV, self).__init__(parent, torrenthandle, num_total_pieces, num_video_pieces, num_video_offset_pieces)

        self.forward_buffer_requested = False     # The forward buffer should only be requested once, after seeking
        self.forward_buffer_available = False     # True if the forward buffer is available, which is the seekPointPieceNumber + bufferSize
        self.forward_buffer_pieces = {}           # Dict of the pieces we are waiting for, in order to determine if the forward buffer is available
        self.header_increase_size_current = 0     # The seekpoint header (not forward buffer) grows by this amount in both directions. headerIncreaseSizeAmount is added every call

    def initialize_pieces(self):

        self.forward_buffer_requested = False
        self.forward_buffer_available = False

        # Set the entire priority list to skip
        piecelist = [0] * self.num_total_pieces # This fills a list of size videoPieces with 0's

        super(TorrentMKV, self).initialize_pieces()

        # Save pieces so we can check them later
        self.pieces[self.current_piece] = False

        # In case we start from the beginning, add a extra buffer so there is less chance of stuttering
        if self.current_piece == self.num_video_offset_pieces:
            for n in range(self.num_video_offset_pieces, self.num_video_offset_pieces + self.buffer_size):
                self.pieces[n] = False

        # Set headers to high priority
        for n in iter(self.pieces):
            piecelist[n] = 1
            self.torrenthandle.set_piece_deadline(n, 5000, 1)   # 1 is alert_when_available

        # Set the list to the torrent handle
        self.torrenthandle.prioritize_pieces(piecelist)

    def update_pieces(self, piece_number):      # TODO incorporate timer that sets deadlines and increases buffer
        super(TorrentMKV, self).update_pieces(piece_number)

        pieces_missing = 0
        for n in iter(self.pieces):
            if not self.pieces[n]:
                pieces_missing += 1

        if not self.forward_buffer_available and self.forward_buffer_requested:
            if self.check_forward_buffer_available(piece_number):
                self.set_forward_buffer_available()

        if self.playable:
            assert self.header_available

        # if header available, the mkv may not yet play. increase the buffer on both ends and keep trying to play.
        if pieces_missing == 0:
            if not self.playable:
                    self.increase_header()

            else: # if header + extra pieces large enough (so actually playing), start sequential download

                    if not self.forward_buffer_requested:
                        self.current_piece += self.header_increase_size_current # add the additional pieces amount
                        self.forward_buffer_pieces = self.increase_buffer(piece_increase_amount=0)
                        self.forward_buffer_requested = True
                    else:
                        self.increase_buffer(piece_increase_amount=self.buffer_size)

    # Increase the header at the front and the back of the header, in order to find the point from where mkv can play.
    def increase_header(self):

        # Deadline in ms for normal pieces
        piece_deadline = 5000

        # Increase the header, this will be reflected in the priorities
        self.header_increase_size_current += self.header_increase_size_amount

        # Create a new list of priorities, initially set to 0 (skip)
        piecelist = [0] * self.num_total_pieces

        # Clear the header piece list, this removes all the pieces (True and False) but the ones that were False
        self.pieces.clear()

        # Increase the header by adding x to the back and x to the front of the header.
        for n in range(self.current_piece, self.current_piece + self.header_increase_size_current):
            if n < self.num_video_pieces + self.num_video_offset_pieces - self.footer_size:
                self.pieces[n] = False  # to keep track of availability
                piecelist[n] = 1    # priority
                self.torrenthandle.set_piece_deadline(n, piece_deadline, 1)     # set deadline and enable alert

        for n in range(self.current_piece - self.header_increase_size_current, self.current_piece):
            if n >= self.num_video_offset_pieces + self.header_size:
                self.pieces[n] = False  # to keep track of availability
                piecelist[n] = 1    # priority
                self.torrenthandle.set_piece_deadline(n, piece_deadline, 1)     # set deadline and enable alert

        # Tell libtorrent to prioritize this list
        self.torrenthandle.prioritize_pieces(piecelist)

    def set_forward_buffer_available(self):
        self.forward_buffer_available = True

        from cloudburst.media.player import Player
        Player.instance().forward_buffer_available = True

        self.parent.set_download_limit(True)

        if self.enable_debug_info:
            print 'Forward buffer available'

    def check_forward_buffer_available(self, piece_number):
        if piece_number in self.forward_buffer_pieces:
            self.forward_buffer_pieces[piece_number] = True

        available = True    # start at True

        for n in iter(self.forward_buffer_pieces):
            if not self.forward_buffer_pieces[n]:
                available = False   # if any piece is false, set available to False

        return available

    def check_header_available(self):
        available = True

        for n in range(self.num_video_offset_pieces, self.num_video_offset_pieces + self.header_size):
            if n in self.pieces:    # if not in pieces, it was set to True and is already removed
                if not self.pieces[n]:
                    available = False

        if self.seekpoint_piece != self.num_video_offset_pieces:    # footer does not get added when playing starts from beginning of file (= 0 + filePiecesOffset), so dont check it
            for n in range(self.num_video_pieces + self.num_video_offset_pieces - self.footer_size, self.num_video_pieces + self.num_video_offset_pieces):
                if n in self.pieces:    # if not in pieces, it was set to True and is already removed
                    if not self.pieces[n]:
                        available = False

        for n in range(self.seekpoint_piece, self.seekpoint_piece + self.buffer_size):
            if n in self.pieces:
                if not self.pieces[n]:
                    available = False

        return available