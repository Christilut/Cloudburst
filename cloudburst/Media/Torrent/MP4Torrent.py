import Torrent


class MP4Torrent(Torrent.Torrent): # inherit from Torrent
    # VARS (can edit)
    # TODO calc buffer size or slowly increasing buffer so it sometimes plays sooner
    # TODO calc header size with mp4file (moov)
    bufferSize = 5          # In pieces, should be a minimum of paddingSize. Since the peers are lost when the header is available,
                            #  the buffer needs to be big enough to re-initialize the torrent (around 10 should do) (based on bitrate)
    headerSize = 5          # Size of the header (first x pieces) (min of 3 for test mp4)
    seekPointSize = 50      # Size of the seekpoint and amount of pieces after it (point + x pieces)
    footerSize = 0          # Size of the footer (last x pieces)

    def __init__(self, parent, torrentHandle, totalPieces, videoPieces, filePiecesOffset):

        super(MP4Torrent, self).__init__(parent, torrentHandle, totalPieces, videoPieces, filePiecesOffset)

        self.firstBufferRequested = False

    def initializePieces(self):

        self.firstBufferRequested = False

        # Set the entire priority list to skip
        pieceList = [0] * self.totalPieces # This fills a list of size videoPieces with 0's

        super(MP4Torrent, self).initializePieces()

        # Save pieces so we can check them later
        if self.seekPointPieceNumber != self.filePiecesOffset: # if not starting at 0
            for n in range(0, self.seekPointSize): # create additional buffer
                self.pieces[self.currentPieceNumber + n] = False

        # Set headers to high priority
        for n in iter(self.pieces):
            pieceList[n] = 1
            self.torrentHandle.set_piece_deadline(n, 5000, 1)   # 1 is alert_when_available

        # Set the list to the torrent handle
        self.torrentHandle.prioritize_pieces(pieceList)

    def isHeaderAvailable(self):
        available = True

        for n in range(self.filePiecesOffset, self.filePiecesOffset + self.headerSize):
            if n in self.pieces: # if not in pieces, it was set to True and is already removed
                if not self.pieces[n]:
                    available = False

        if self.seekPointPieceNumber != self.filePiecesOffset: # footer does not get added when playing starts from beginning of file (= 0 + filePiecesOffset), so dont check it
            for n in range(self.videoPieces + self.filePiecesOffset - self.footerSize, self.videoPieces + self.filePiecesOffset):
                if n in self.pieces: # if not in pieces, it was set to True and is already removed
                    if not self.pieces[n]:
                        available = False

        for n in range(self.seekPointPieceNumber, self.seekPointPieceNumber + self.seekPointSize):
            if n in self.pieces:
                if not self.pieces[n]:
                    available = False

        return available

    # When header is in, call this function. Start to play movie and enable custom sequential download
    def setHeaderAvailable(self, available):
        super(MP4Torrent, self).setHeaderAvailable(available)

        if available:
            self.parent.setDownloadLimit(True)


    def updatePieceList(self, pieceNumber): # TODO incorporate timer that sets deadlines and increases buffer
        super(MP4Torrent, self).updatePieceList(pieceNumber)

        piecesMissing = 0
        for n in iter(self.pieces):
            if not self.pieces[n]:
                piecesMissing += 1

        if not self.headerAvailable:
            if self.isHeaderAvailable():
                self.setHeaderAvailable(True)

        # if all pieces we currently want are downloaded
        if self.headerAvailable and piecesMissing == 0:

            if not self.firstBufferRequested:
                self.increaseBuffer(increasePiecePosition=self.headerSize)
                self.firstBufferRequested = True
            else:
                self.increaseBuffer(increasePiecePosition=self.bufferSize)