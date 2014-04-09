import torrent


class TorrentMP4(torrent.Torrent):  # inherit from Torrent
    # VARS (can edit)
    # TODO calc buffer size or slowly increasing buffer so it sometimes plays sooner
    # TODO calc header size with mp4file (moov)
    bufferSize = 5          # In pieces, should be a minimum of paddingSize. Since the peers are lost when the header is available,
                            #  the buffer needs to be big enough to re-initialize the torrent (around 10 should do) (based on bitrate)
    headerSize = 5          # Size of the header (first x pieces) (min of 3 for test mp4)
    seekPointSize = 50      # Size of the seekpoint and amount of pieces after it (point + x pieces)
    footerSize = 0          # Size of the footer (last x pieces)

    def __init__(self, parent, torrenthandle, num_total_pieces, num_video_pieces, num_video_offset_pieces):
        super(TorrentMP4, self).__init__(parent, torrenthandle, num_total_pieces, num_video_pieces, num_video_offset_pieces)

        self.first_buffer_requested = False

    def initialize_pieces(self):

        self.first_buffer_requested = False

        # Set the entire priority list to skip
        piecelist = [0] * self.num_total_pieces     # This fills a list of size videoPieces with 0's

        super(TorrentMP4, self).initialize_pieces()

        # Save pieces so we can check them later
        if self.seekpoint_piece != self.num_video_offset_pieces:    # if not starting at 0
            for n in range(0, self.seekPointSize):  # create additional buffer
                self.pieces[self.current_piece + n] = False

        # Set headers to high priority
        for n in iter(self.pieces):
            piecelist[n] = 1
            self.torrenthandle.set_piece_deadline(n, 5000, 1)   # 1 is alert_when_available

        # Set the list to the torrent handle
        self.torrenthandle.prioritize_pieces(piecelist)

    def check_header_available(self):
        available = True

        for n in range(self.num_video_offset_pieces, self.num_video_offset_pieces + self.headerSize):
            if n in self.pieces:    # if not in pieces, it was set to True and is already removed
                if not self.pieces[n]:
                    available = False

        if self.seekpoint_piece != self.num_video_offset_pieces:    # footer does not get added when playing starts from beginning of file (= 0 + filePiecesOffset), so dont check it
            for n in range(self.num_video_pieces + self.num_video_offset_pieces - self.footerSize, self.num_video_pieces + self.num_video_offset_pieces):
                if n in self.pieces:    # if not in pieces, it was set to True and is already removed
                    if not self.pieces[n]:
                        available = False

        for n in range(self.seekpoint_piece, self.seekpoint_piece + self.seekPointSize):
            if n in self.pieces:
                if not self.pieces[n]:
                    available = False

        return available

    # When header is in, call this function. Start to play movie and enable custom sequential download
    def set_header_available(self, available):
        super(TorrentMP4, self).set_header_available(available)

        if available:
            self.parent.set_download_limit(True)

    def update_pieces(self, piece_number):  # TODO incorporate timer that sets deadlines and increases buffer
        super(TorrentMP4, self).update_pieces(piece_number)

        pieces_missing = 0
        for n in iter(self.pieces):
            if not self.pieces[n]:
                pieces_missing += 1

        if not self.header_available:
            if self.check_header_available():
                self.set_header_available(True)

        # if all pieces we currently want are downloaded
        if self.header_available and pieces_missing == 0:

            if not self.first_buffer_requested:
                self.increase_buffer(piece_increase_amount=self.headerSize)
                self.first_buffer_requested = True
            else:
                self.increase_buffer(piece_increase_amount=self.bufferSize)