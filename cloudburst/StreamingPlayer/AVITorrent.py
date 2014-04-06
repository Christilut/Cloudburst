import Torrent


class AVITorrent(Torrent.Torrent): # inherit from Torrent
    # VARS (can edit)

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

        if self.currentPieceNumber < self.filePiecesOffset:
            self.currentPieceNumber = self.filePiecesOffset

        # Set the entire priority list to skip
        pieceList = [0] * self.totalPieces # This fills a list of size videoPieces with 0's

        # Save pieces so we can check them later
        self.headerPieces[self.currentPieceNumber] = False

        # Save how many we set for later
        self.headerPiecesRequired = len(self.headerPieces)

        # Set headers to high priority
        for n in iter(self.headerPieces):
            pieceList[n] = 1
            self.torrentHandle.set_piece_deadline(n, 5000, 1)   # 1 is alert_when_available

        # Set the list to the torrent handle
        self.torrentHandle.prioritize_pieces(pieceList)

    def updatePieceList(self, pieceNumber): # TODO incorporate timer that sets deadlines and increases buffer
        if self.enableDebugInfo:
            print 'Updated piece', pieceNumber


        if not self.forwardBufferAvailable and self.forwardBufferRequested:
            if self.isForwardBufferAvailable(pieceNumber):
                self.setForwardBufferAvailable()

        if pieceNumber in self.pieces:
            if not self.pieces[pieceNumber]:
                self.pieces[pieceNumber] = True

        if pieceNumber in self.headerPieces:
            if not self.headerPieces[pieceNumber]:
                self.headerPieces[pieceNumber] = True

        pieceAvailableCount = 0
        for n in iter(self.pieces):
            if self.pieces[n]:
                pieceAvailableCount += 1

        headerPieceAvailableCount = 0
        for n in iter(self.headerPieces):
            if self.headerPieces[n]:
                headerPieceAvailableCount += 1

        if not self.headerAvailable:
            if self.isHeaderAvailable():
                self.setHeaderAvailable(True)
                return # dont add new pieces, wait for player


        if self.parent.parent.canPlay: # TODO fix this nastyness
            assert self.headerAvailable

        # if header available, the mkv may not yet play. increase the buffer on both ends and keep trying to play.
        if not self.parent.parent.canPlay:

            if headerPieceAvailableCount >= (self.headerPiecesRequired - self.headerIncreaseOffset):
                missingPieces = []
                for n in iter(self.headerPieces):
                    if not self.headerPieces[n]:
                        missingPieces.append(n)

                self.increaseHeader(missingPieces)

        else: # if header + extra pieces large enough (so actually playing), start sequential download

            if pieceAvailableCount >= (self.piecesRequired - self.paddingSize): # x pieces left

                missingPieces = []

                # the header may still contain some missing pieces, add them the first time this is called
                if not self.headerPiecesAddedToBuffer:
                    self.headerPiecesAddedToBuffer = True

                    for n in iter(self.headerPieces):
                        if not self.headerPieces[n]:
                            missingPieces.append(n)

                # and get the missing pieces from the regular pieces
                for n in iter(self.pieces):
                    if not self.pieces[n]:
                        missingPieces.append(n)

                # add missing piece as argument so they can be prioritized
                if not self.forwardBufferRequested:
                    self.currentPieceNumber += self.headerIncreaseSizeCurrent # add the additional pieces amount
                    self.forwardBufferPieces = self.increaseBuffer(missingPieces=missingPieces, increasePiecePosition=False)
                    self.forwardBufferRequested = True
                else:
                    self.increaseBuffer(missingPieces=missingPieces)

    # Increase the header at the front and the back of the header, in order to find the point from where mkv can play.
    # The missingPieces argument contains pieces that were not yet in and will be priotized.
    def increaseHeader(self, missingPieces = None):

        # Deadline in ms for normal pieces (not the missing ones)
        pieceDeadlineTime = 5000

        # Increase the header, this will be reflected in the priorities
        self.headerIncreaseSizeCurrent += 1

        # Create a new list of priorities, initially set to 0 (skip)
        pieceList = [0] * self.totalPieces

        # Clear the header piece list, this removes all the pieces (True and False) but the ones that were False, are the missingPieces and will be added again
        self.headerPieces.clear()

        if missingPieces is not None:

            for n in range(0, len(missingPieces)):

                higherPriority = 2 # The priority for missing pieces

                # Make sure header pieces get even higher priority, since the video must wait for these before starting
                if missingPieces[n] > self.videoPieces + self.filePiecesOffset - self.footerSize - 1 or missingPieces[n] < self.filePiecesOffset + self.headerSize:
                    higherPriority = 3 # The priority for missing header pieces
                    pieceDeadlineTime = 2000

                pieceList[missingPieces[n]] = higherPriority # higher priority

                self.headerPieces[missingPieces[n]] = False
                self.torrentHandle.set_piece_deadline(missingPieces[n], pieceDeadlineTime, 1)

        # Increase the header by adding x to the back and x to the front of the header.
        pieceFront = self.currentPieceNumber + self.headerIncreaseSizeCurrent
        pieceBack = self.currentPieceNumber - self.headerIncreaseSizeCurrent

        if pieceFront < self.videoPieces + self.filePiecesOffset - self.footerSize:
            self.headerPieces[pieceFront] = False # to keep track of availability
            pieceList[pieceFront] = 1 # priority
            self.torrentHandle.set_piece_deadline(pieceFront, pieceDeadlineTime, 1) # set deadline and enable alert

        if pieceBack >= self.filePiecesOffset + self.headerSize:
            self.headerPieces[pieceBack] = False # to keep track of availability
            pieceList[pieceBack] = 1 # priority
            self.torrentHandle.set_piece_deadline(pieceBack, pieceDeadlineTime, 1) # set deadline and enable alert

        # Save the amount of pieces that we currently want
        self.headerPiecesRequired = len(self.headerPieces)

        # Tell libtorrent to prioritize this list
        self.torrentHandle.prioritize_pieces(pieceList)

    def setForwardBufferAvailable(self):
        self.forwardBufferAvailable = True
        self.parent.parent.forwardBufferAvailable = True

        self.parent.setDownloadLimit(True)

        print 'Forward buffer available'

    def isForwardBufferAvailable(self, pieceNumber):

        if pieceNumber in self.forwardBufferPieces:
            self.forwardBufferPieces[pieceNumber] = True

        available = True
        for n in iter(self.forwardBufferPieces):
            if not self.forwardBufferPieces[n]:
                available = False

        return available