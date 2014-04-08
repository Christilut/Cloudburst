import Torrent


class MKVTorrent(Torrent.Torrent): # inherit from Torrent
    # VARS (can edit)

    bufferSize = 5 # in pieces, should be a minimum of paddingSize. Since the peers are lost when the header is available, the buffer needs to be big enough to re-initialize the torrent (around 10 should do) (based on bitrate)
    seekPointOffset = 0

    headerSize = 1 # size of the header (first x pieces)
    footerSize = 1 # size of the footer (last x pieces)

    headerIncreaseSizeAmount = 2 # this many pieces are added to the front AND the back of the header buffer
    headerIncreaseOffset = 1 # if this many pieces are missing from the header, headerIncreaseSizeAmount amount are added. Must be higher than headerIncreaseSizeAmount

    # ATTRIBUTES (do not edit)

    forwardBufferRequested = False
    forwardBufferAvailable = False
    forwardBufferPieces = {}

    headerIncreaseSizeCurrent = 0 # starting value, do not edit # TODO figure out what to do with values that need not be edited


    def __init__(self, parent, torrentHandle):

        super(MKVTorrent, self).__init__(parent, torrentHandle)

    def initializePieces(self):

        self.forwardBufferRequested = False
        self.forwardBufferAvailable = False

        # Set the entire priority list to skip
        pieceList = [0] * self.totalPieces # This fills a list of size videoPieces with 0's

        super(MKVTorrent, self).initializePieces()

        # Save pieces so we can check them later
        self.pieces[self.currentPieceNumber] = False

        # In case we start from the beginning, add a extra buffer so there is less chance of stuttering
        if self.currentPieceNumber == self.filePiecesOffset:
            for n in range(self.filePiecesOffset, self.filePiecesOffset + self.bufferSize):
                self.pieces[n] = False

        # Set headers to high priority
        for n in iter(self.pieces):
            pieceList[n] = 1
            self.torrentHandle.set_piece_deadline(n, 5000, 1)   # 1 is alert_when_available

        # Set the list to the torrent handle
        self.torrentHandle.prioritize_pieces(pieceList)

    def updatePieceList(self, pieceNumber): # TODO incorporate timer that sets deadlines and increases buffer

        super(MKVTorrent, self).updatePieceList(pieceNumber)

        piecesMissing = 0
        for n in iter(self.pieces):
            if not self.pieces[n]:
                piecesMissing += 1

        if not self.forwardBufferAvailable and self.forwardBufferRequested:
            if self.isForwardBufferAvailable(pieceNumber):
                self.setForwardBufferAvailable()

        if self.parent.parent.canPlay: # TODO fix this nastyness
            assert self.headerAvailable

        # if header available, the mkv may not yet play. increase the buffer on both ends and keep trying to play.
        if piecesMissing == 0:
            if not self.parent.parent.canPlay:
                    self.increaseHeader()

            else: # if header + extra pieces large enough (so actually playing), start sequential download

                    if not self.forwardBufferRequested:
                        self.currentPieceNumber += self.headerIncreaseSizeCurrent # add the additional pieces amount
                        self.forwardBufferPieces = self.increaseBuffer(increasePiecePosition=0)
                        self.forwardBufferRequested = True
                    else:
                        self.increaseBuffer(increasePiecePosition=self.bufferSize)

    # Increase the header at the front and the back of the header, in order to find the point from where mkv can play.
    # The missingPieces argument contains pieces that were not yet in and will be priotized.
    def increaseHeader(self):

        # Deadline in ms for normal pieces (not the missing ones)
        pieceDeadlineTime = 5000

        # Increase the header, this will be reflected in the priorities
        self.headerIncreaseSizeCurrent += self.headerIncreaseSizeAmount

        # Create a new list of priorities, initially set to 0 (skip)
        pieceList = [0] * self.totalPieces

        # Clear the header piece list, this removes all the pieces (True and False) but the ones that were False, are the missingPieces and will be added again
        self.pieces.clear()

        # Increase the header by adding x to the back and x to the front of the header.
        for n in range(self.currentPieceNumber, self.currentPieceNumber + self.headerIncreaseSizeCurrent):
            if n < self.videoPieces + self.filePiecesOffset - self.footerSize:
                self.pieces[n] = False # to keep track of availability
                pieceList[n] = 1 # priority
                self.torrentHandle.set_piece_deadline(n, pieceDeadlineTime, 1) # set deadline and enable alert

        for n in range(self.currentPieceNumber - self.headerIncreaseSizeCurrent, self.currentPieceNumber):
            if n >= self.filePiecesOffset + self.headerSize:
                self.pieces[n] = False # to keep track of availability
                pieceList[n] = 1 # priority
                self.torrentHandle.set_piece_deadline(n, pieceDeadlineTime, 1) # set deadline and enable alert

        # Tell libtorrent to prioritize this list
        self.torrentHandle.prioritize_pieces(pieceList)

    def setForwardBufferAvailable(self):
        self.forwardBufferAvailable = True
        self.parent.parent.forwardBufferAvailable = True

        self.parent.setDownloadLimit(True)

        if self.enableDebugInfo:
            print 'Forward buffer available'

    def isForwardBufferAvailable(self, pieceNumber):

        if pieceNumber in self.forwardBufferPieces:
            self.forwardBufferPieces[pieceNumber] = True

        available = True # start at True

        for n in iter(self.forwardBufferPieces):
            if not self.forwardBufferPieces[n]:
                available = False # if any piece is false, set available to False

        return available

    def isHeaderAvailable(self):
        available = True

        super(MKVTorrent, self).isHeaderAvailable()

        for n in range(self.seekPointPieceNumber, self.seekPointPieceNumber + self.bufferSize):
            if n in self.pieces:
                if not self.pieces[n]:
                    available = False

        return available