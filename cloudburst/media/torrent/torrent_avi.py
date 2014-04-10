import torrent


class TorrentAVI(torrent.Torrent):  # inherit from Torrent
    # VARS (can edit)
    # TODO calc buffer size or slowly increasing buffer so it sometimes plays sooner
    buffer_size = 5  # in pieces, should be a minimum of paddingSize. Since the peers are lost when the header is available, \
                    # the buffer needs to be big enough to re-initialize the torrent (around 10 should do) (based on bitrate)

    def __init__(self, parent, torrenthandle, num_total_pieces, num_video_pieces, num_video_offset_pieces):
        super(TorrentAVI, self).__init__(parent, torrenthandle, num_total_pieces, num_video_pieces, num_video_offset_pieces)

    def _initialize_pieces(self):

        # Check cache once, in case the file already existed
        # self._checkCache()     # TODO test this works

        # Header pieces
        for n in range(self.num_video_offset_pieces, self.num_video_offset_pieces + self.buffer_size):
            self.pieces[n] = False                  # start of the file

        # Set the entire priority list to skip
        piecelist = [0] * self.num_total_pieces     # This fills a list of size videoPieces with 0's

        # Set headers to high priority
        for n in iter(self.pieces):
            piecelist[n] = 1
            self.torrenthandle.set_piece_deadline(n, 5000, 1)   # 1 is alert_when_available

        # Set the list to the torrent handle
        self.torrenthandle.prioritize_pieces(piecelist)

    # When header is in, call this function. Start to play movie and enable custom sequential download
    def set_header_available(self, available):
        super(TorrentAVI, self).set_header_available(available)

        if available:
            self.parent.set_download_limit(True)

    def _check_header_available(self):   # do not call super. Avi can only start from 0
        available = True

        for n in range(self.num_video_offset_pieces, self.num_video_offset_pieces + self.buffer_size):
            if n in self.pieces:    # if not in pieces, it was set to True and is already removed
                if not self.pieces[n]:
                    available = False

        return available

    def update_pieces(self, piece_number):  # TODO incorporate timer that sets deadlines and increases buffer
        super(TorrentAVI, self).update_pieces(piece_number)

        pieces_missing = 0
        for n in iter(self.pieces):
            if not self.pieces[n]:
                pieces_missing += 1

        if not self.header_available:
            if self._check_header_available():
                self.set_header_available(True)

        # if all pieces we currently want are downloaded
        if self.header_available and pieces_missing == 0:

            self._increase_buffer(piece_increase_amount=self.buffer_size)

    def set_video_position(self, position):
        print 'AVI does not support seeking'

    def set_seekpoint(self, seekpoint):
        print 'AVI does not support seeking'