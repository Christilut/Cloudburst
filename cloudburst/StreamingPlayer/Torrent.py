import libtorrent as lt
import threading
import time

class Torrent():

    # CONFIG VARS (can edit)
    # TODO base buffersize on bitrate and pieceSize
    paddingSize = 3 # when this many pieces are left missing, the buffer is increased



    enableDebugInfo = True

    # ATTRIBUTES (do not edit)

    torrentHandle = None
    torrentStatus = None

    isRunning = False

    seekPointPieceNumber = 0 # TODO turn into properties, readonly
    currentPieceNumber = 0
    seekPoint = 0 # from 0 to 1
    videoPieces = -1 # Total amount of pieces in the torrent
    headerAvailable = False
    filePiecesOffset = 0 # Amount of pieces the video file is offset by. These pieces include all skipped files before the video

    totalPieces  = -1 # Total amount of pieces in the torrent

    pieces = {}
    headerPieces = {}
    piecesRequired = 0
    headerPiecesRequired = 0


    def __init__(self, parent, torrentHandle):

        self.parent = parent
        self.torrentHandle = torrentHandle

        # Some sanity checks
        assert self.bufferSize >= self.paddingSize
        # TODO add more

        self.isRunning = True

    def shutdown(self):
        self.isRunning = False

    # Start the torrent and the required threads
    def startTorrent(self, seekpoint, totalPieces, videoPieces, filePiecesOffset ):

        assert seekpoint is not None

        self.seekPoint = seekpoint
        self.totalPieces = totalPieces
        self.videoPieces = videoPieces
        self.filePiecesOffset = filePiecesOffset

        self.initializePieces()

        # start download thread
        downloadThread = threading.Thread(target=self.threadTorrentInfo)
        downloadThread.daemon = True
        downloadThread.start()


    # Check which pieces already exist in an existing file, if available
    def checkCache(self):
        for n in iter(self.pieces):
            if self.torrentHandle.have_piece(n):
                if self.pieces[n]:
                    self.updatePieceList(n)

    def getBytesDownloaded(self):
        return self.torrentStatus.total_wanted_done

    def getBytesWanted(self):
        return self.torrentStatus.total_wanted

    def printTorrentDebug(self):

        infoSize = 20

        print 'Avail.\t:',

        # Header
        for n in range(self.filePiecesOffset, self.filePiecesOffset + self.headerSize):
            if self.torrentHandle.have_piece(n):
                print '1',
            else:
                print '0',

        print '#',

        # Seekpoint
        for n in range(max(self.seekPointPieceNumber - infoSize, self.filePiecesOffset), min(self.seekPointPieceNumber + infoSize, self.videoPieces + self.filePiecesOffset - 1)):
            if self.torrentHandle.have_piece(n):
                print '1',
            else:
                print '0',

        print '#',

        # Footer
        for n in range(0, self.footerSize):
            if self.torrentHandle.have_piece(self.videoPieces + self.filePiecesOffset - 1 - n):
                print '1',
            else:
                print '0',

        print ''

        # Priorities

        print 'Prior.\t:',
        # Header
        for n in range(self.filePiecesOffset, self.filePiecesOffset + self.headerSize):
            if self.torrentHandle.piece_priority(n):
                print '1',
            else:
                print '0',

        print '#',

        # Seekpoint
        for n in range(max(self.seekPointPieceNumber - infoSize, self.filePiecesOffset), min(self.seekPointPieceNumber + infoSize, self.videoPieces + self.filePiecesOffset - 1)):
            if self.torrentHandle.piece_priority(n):
                print '1',
            else:
                print '0',

        print '#',

        # Footer
        for n in range(0, self.footerSize):
            if self.torrentHandle.piece_priority(self.videoPieces + self.filePiecesOffset - 1 - n):
                print '1',
            else:
                print '0',

        print ''

    # Sets the torrent to download the video data starting from the seekpoint
    def increaseBuffer(self, increasePiecePosition, missingPieces = None):

        # Deadline in ms for normal pieces (not the missing ones)
        pieceDeadlineTime = 5000

        # Increase the buffer, this will be reflected in the priorities
        self.currentPieceNumber += increasePiecePosition

        # Create a new list of priorities, initially set to 0 (skip)
        pieceList = [0] * self.totalPieces

        # Clear the buffer piece list, this removes all the pieces (True and False) but the ones that were False, are the missingPieces and will be added again
        self.pieces.clear()

        if missingPieces is not None:

            for n in range(0, len(missingPieces)):

                higherPriority = 2 # The priority for missing pieces
                pieceDeadlineTime = 2000 # Deadline time in ms

                pieceList[missingPieces[n]] = higherPriority # higher priority

                self.pieces[missingPieces[n]] = False # Add them to the list
                self.torrentHandle.set_piece_deadline(missingPieces[n], pieceDeadlineTime, 1) # Set deadline and enable alert

        # Now handle the increase of the buffer
        for n in range(0, self.bufferSize):

            targetPiece = self.currentPieceNumber + n

            if targetPiece < self.videoPieces: # dont go beyond the pieces of the video file
                piece = self.currentPieceNumber + n

                self.pieces[piece] = False # Add to the list
                pieceList[piece] = 1 # Set priority
                self.torrentHandle.set_piece_deadline(piece, pieceDeadlineTime, 1) # Set deadline and enable alert

        # Save the amount of pieces that we currently want
        self.piecesRequired = len(self.pieces) # TODO not used anymore?

        # Tell libtorrent to prioritize this list
        self.torrentHandle.prioritize_pieces(pieceList)

        # Return the list but use a copy otherwise a reference is used which will reflect changes in both ends
        return self.pieces.copy()


    # Seekpoint is the float from 0 to 1 where the video should play from
    def setVideoPosition(self, position):

        if self.enableDebugInfo:
            print 'Seekpoint set to:', position

        self.setSeekpoint(position)

        self.setHeaderAvailable(False)

        self.initializePieces()

    def setSeekpoint(self, seekpoint):
        # Seekpoint position
        self.seekPoint = seekpoint
        self.currentPieceNumber = int(float(self.videoPieces) / 1 * seekpoint) + self.filePiecesOffset + self.seekPointOffset
        self.seekPointPieceNumber = self.currentPieceNumber

    def threadTorrentInfo(self): # thread

        while not self.torrentHandle.is_seed() and self.isRunning: # while not finished
            self.torrentStatus = self.torrentHandle.status()

            if self.torrentStatus.progress != 1:
                state_str = ['queued', 'checking', 'downloading metadata',
                        'downloading', 'finished', 'seeding', 'allocating', 'checking fastresume']
                print '\rdown: %.1f kB/s, peers: %d, status: %s' % \
                    (self.torrentStatus.download_rate / 1000,
                    self.torrentStatus.num_peers, state_str[self.torrentStatus.state])

            if self.enableDebugInfo:
                self.printTorrentDebug()

            time.sleep(3)