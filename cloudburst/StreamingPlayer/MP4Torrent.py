import Torrent


class MP4Torrent(Torrent.Torrent): # inherit from Torrent
    # VARS (can edit)
    # TODO calc buffer size or slowly increasing buffer so it sometimes plays sooner
    bufferSize = 5 # in pieces, should be a minimum of paddingSize. Since the peers are lost when the header is available, the buffer needs to be big enough to re-initialize the torrent (around 10 should do) (based on bitrate)
    seekPointOffset = 0
    # TODO calc header size with mp4file (moov)
    headerSize = 3 # size of the header (first x pieces) (min of 3 for test mp4)
    seekPointSize = 50 # size of the seekpoint and amount of pieces after it (point + x pieces)
    footerSize = 0 # size of the footer (last x pieces)

    headerIncreaseSizeAmount = 1 # this many pieces are added to the front AND the back of the header buffer
    headerIncreaseOffset = 1 # if this many pieces are missing from the header, headerIncreaseSizeAmount amount are added. Must be higher than headerIncreaseSizeAmount

    # ATTRIBUTES (do not edit)

    forwardBufferRequested = False
    forwardBufferAvailable = False
    forwardBufferPieces = {}

    headerIncreaseSizeCurrent = 0 # starting value, do not edit # TODO figure out what to do with values that need not be edited
    headerPiecesAddedToBuffer = False


    def __init__(self, parent, torrentHandle):

        Torrent.Torrent.__init__(self, parent, torrentHandle)

        self.firstBufferRequested = False

    def initializePieces(self):

        # Reset some vars incase of seeking
        self.parent.setDownloadLimit(False)
        self.piecesRequired = 0
        self.headerPiecesAddedToBuffer = False
        self.headerIncreaseSizeCurrent = 0
        self.forwardBufferRequested = False
        self.forwardBufferAvailable = False

        # Check cache once, in case the file already existed
        # self.checkCache() # TODO test this works

        # Seekpoint position
        # self.currentPieceNumber = int(float(self.videoPieces) / 1 * self.seekPoint) + self.filePiecesOffset
        # self.seekPointPieceNumber = self.currentPieceNumber
        self.setSeekpoint(self.seekPoint)

        # Clear header list incase of seeking an already playing video
        self.headerPieces.clear()

        # Header pieces
        for n in range(self.filePiecesOffset, self.filePiecesOffset + self.headerSize):
            self.headerPieces[n] = False                # start of the file

        # Footer size (MKV Cueing data)
        # if self.seekPointPieceNumber > self.filePiecesOffset: # footer is only required for seeking # TODO make sure the footer does get downloaded when seeking after playing from 0
        for n in range(0, self.footerSize):
            self.headerPieces[self.videoPieces + self.filePiecesOffset - 1 - n] = False  # end of the file (MKV needs this) # TODO not needed for avi?

        if self.enableDebugInfo:
            print 'Seekpoint piece:', self.seekPointPieceNumber

        # Make sure the current piece cant go below the first piece of the video
        if self.currentPieceNumber < self.filePiecesOffset:
            self.currentPieceNumber = self.filePiecesOffset

        # Set the entire priority list to skip
        pieceList = [0] * self.totalPieces # This fills a list of size videoPieces with 0's

        # Save pieces so we can check them later
        if self.seekPointPieceNumber != 0: # if not starting at 0
            for n in range(0, self.seekPointSize): # create additional buffer
                self.headerPieces[self.currentPieceNumber + n] = False

        # Save how many we set for later
        self.headerPiecesRequired = len(self.headerPieces)

        # Set headers to high priority
        for n in iter(self.headerPieces):
            pieceList[n] = 1
            self.torrentHandle.set_piece_deadline(n, 5000, 1)   # 1 is alert_when_available

        # Set the list to the torrent handle
        self.torrentHandle.prioritize_pieces(pieceList)

    # When header is in, call this function. Start to play movie and enable custom sequential download
    def setHeaderAvailable(self, available):
        self.parent.parent.setHeaderAvailable(available)
        self.headerAvailable = available
        self.parent.setDownloadLimit(True)

        if self.enableDebugInfo:
            print 'Header available?', available
            self.printTorrentDebug()

    def isHeaderAvailable(self):
        available = True

        for n in range(self.filePiecesOffset, self.filePiecesOffset + self.headerSize):
            if n in self.headerPieces: # if not in headerPieces, it was set to True and is already removed
                if not self.headerPieces[n]:
                    available = False

        for n in range(self.seekPointPieceNumber, self.seekPointPieceNumber + self.bufferSize):
            if n in self.headerPieces:
                if not self.headerPieces[n]:
                    available = False

        if self.seekPointPieceNumber != self.filePiecesOffset: # footer does not get added when playing starts from beginning of file (= 0 + filePiecesOffset), so dont check it
            for n in range(self.videoPieces + self.filePiecesOffset - self.footerSize, self.videoPieces + self.filePiecesOffset):
                if n in self.headerPieces: # if not in headerPieces, it was set to True and is already removed
                    if not self.headerPieces[n]:
                        available = False

        return available

    def updatePieceList(self, pieceNumber): # TODO incorporate timer that sets deadlines and increases buffer
        if self.enableDebugInfo:
            print 'Updated piece', pieceNumber

        if pieceNumber in self.pieces:
            if not self.pieces[pieceNumber]:
                self.pieces[pieceNumber] = True

        if pieceNumber in self.headerPieces:
            if not self.headerPieces[pieceNumber]:
                self.headerPieces[pieceNumber] = True

        piecesMissing = 0
        for n in iter(self.pieces):
            if not self.pieces[n]:
                piecesMissing += 1

        if not self.headerAvailable:
            headerPieceAvailableCount = 0
            for n in iter(self.headerPieces):
                if self.headerPieces[n]:
                    headerPieceAvailableCount += 1

            if self.isHeaderAvailable():
                self.setHeaderAvailable(True)

        # if all pieces we currently want are downloaded
        if self.headerAvailable and piecesMissing == 0:

            if self.firstBufferRequested == False:
                self.increaseBuffer(increasePiecePosition=self.headerSize)
                self.firstBufferRequested = True
            else:
                self.increaseBuffer(increasePiecePosition=self.bufferSize)