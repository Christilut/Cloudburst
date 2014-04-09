import Torrent


class AVITorrent(Torrent.Torrent): # inherit from Torrent
    # VARS (can edit)
    # TODO calc buffer size or slowly increasing buffer so it sometimes plays sooner
    bufferSize = 5 # in pieces, should be a minimum of paddingSize. Since the peers are lost when the header is available, the buffer needs to be big enough to re-initialize the torrent (around 10 should do) (based on bitrate)


    def __init__(self, parent, torrentHandle, totalPieces, videoPieces, filePiecesOffset):

        super(AVITorrent, self).__init__(parent, torrentHandle, totalPieces, videoPieces, filePiecesOffset)

    def initializePieces(self):

        # Check cache once, in case the file already existed
        # self.checkCache() # TODO test this works

        # Header pieces
        for n in range(self.filePiecesOffset, self.filePiecesOffset + self.bufferSize):
            self.pieces[n] = False                # start of the file

        # Set the entire priority list to skip
        pieceList = [0] * self.totalPieces # This fills a list of size videoPieces with 0's

        # Set headers to high priority
        for n in iter(self.pieces):
            pieceList[n] = 1
            self.torrentHandle.set_piece_deadline(n, 5000, 1)   # 1 is alert_when_available

        # Set the list to the torrent handle
        self.torrentHandle.prioritize_pieces(pieceList)

    # When header is in, call this function. Start to play movie and enable custom sequential download
    def setHeaderAvailable(self, available):
        super(AVITorrent, self).setHeaderAvailable(available)

        if available:
            self.parent.setDownloadLimit(True)

    def isHeaderAvailable(self): # do not call super. Avi can only start from 0
        available = True

        for n in range(self.filePiecesOffset, self.filePiecesOffset + self.bufferSize):
            if n in self.pieces: # if not in pieces, it was set to True and is already removed
                if not self.pieces[n]:
                    available = False

        return available

    def updatePieceList(self, pieceNumber): # TODO incorporate timer that sets deadlines and increases buffer
        super(AVITorrent, self).updatePieceList(pieceNumber)

        piecesMissing = 0
        for n in iter(self.pieces):
            if not self.pieces[n]:
                piecesMissing += 1

        if not self.headerAvailable:
            if self.isHeaderAvailable():
                self.setHeaderAvailable(True)

        # if all pieces we currently want are downloaded
        if self.headerAvailable and piecesMissing == 0:

            self.increaseBuffer(increasePiecePosition=self.bufferSize)

    def setVideoPosition(self, position):
        print 'AVI does not support seeking'

    def setSeekpoint(self, seekpoint):
        print 'AVI does not support seeking'