import threading
import time

class Torrent(object):

    # CONFIG VARS (can edit)
    # TODO base buffersize on bitrate and pieceSize
    paddingSize = 3 # when this many pieces are left missing, the buffer is increased

    enableDebugInfo = True


    def __init__(self, parent, torrentHandle, totalPieces, videoPieces, filePiecesOffset):

        self.parent = parent
        self.torrentHandle = torrentHandle
        self.totalPieces = totalPieces              # Total amount of pieces in the torrent
        self.videoPieces = videoPieces              # Total amount of pieces in the video file
        self.filePiecesOffset = filePiecesOffset    # Amount of pieces the video file is offset by. These pieces include all skipped files before the video

        # Init vars, do not edit
        self.torrentStatus = None       # Status object of the torrent, obtained from libtorrent
        self.isRunning = False          # if the torrent has been started # TODO
        self.seekPointPieceNumber = 0   # The piece that corresponds with the seekPoint
        self.currentPieceNumber = 0     # current piece the torrent should be downloading (+ bufferSize)
        self.seekPoint = 0              # from 0 to 1, point where the video wishes to play from
        self.headerAvailable = False    # True if the header, footer and seekpoint are available
        self.pieces = {}                # Dict of the pieces that we are waiting for
        self.playable = False

        # Some sanity checks
        assert self.bufferSize >= self.paddingSize
        # TODO add more

        self.isRunning = True

        # start thread that displays torrent info
        downloadThread = threading.Thread(target=self.threadTorrentInfo)
        downloadThread.daemon = True
        downloadThread.start()

        # Download is not started yet but torrent is active. This results in finding peers without downloading.


    def shutdown(self):
        self.isRunning = False

    # Start the torrent. This will enable pieces and actually start the download.
    def start(self, seekpoint):

        # Seekpoint position
        self.seekPoint = seekpoint
        self.currentPieceNumber = int(float(self.videoPieces) / 1 * seekpoint) + self.filePiecesOffset
        self.seekPointPieceNumber = self.currentPieceNumber

        self.setHeaderAvailable(False)

        # Determine which pieces are wanted
        self.initializePieces()

    # Check which pieces already exist in an existing file, if available
    def checkCache(self):
        for n in iter(self.pieces):
            if self.torrentHandle.have_piece(n):
                if self.pieces[n]:
                    self.updatePieceList(n)

    def setPlayable(self, playable):
        self.playable = playable

    def getBytesDownloaded(self):
        return self.torrentStatus.total_wanted_done

    def getBytesWanted(self):
        return self.torrentStatus.total_wanted

    def printTorrentDebug(self):

        infoSize = 55

        print 'Avail.\t(', self.currentPieceNumber, ')\t:',

        # Header
        if hasattr(self, 'headerSize') and self.headerSize != 0:
            for n in range(self.filePiecesOffset, self.filePiecesOffset + self.headerSize):
                if self.torrentHandle.have_piece(n):
                    print '1',
                else:
                    print '0',

            print '#',

        # Seekpoint
        for n in range(max(self.currentPieceNumber - infoSize, self.filePiecesOffset), min(self.currentPieceNumber + infoSize, self.videoPieces + self.filePiecesOffset - 1)):
            if self.torrentHandle.have_piece(n):
                print '1',
            else:
                print '0',

        # Footer
        if hasattr(self, 'footerSize') and self.footerSize != 0:
            print '#',
            for n in range(0, self.footerSize):
                if self.torrentHandle.have_piece(self.videoPieces + self.filePiecesOffset - 1 - n):
                    print '1',
                else:
                    print '0',

        print ''

        # Priorities
        print 'Prior.\t\t\t:',

        # Header
        if hasattr(self, 'headerSize') and self.headerSize != 0:
            for n in range(self.filePiecesOffset, self.filePiecesOffset + self.headerSize):
                if self.torrentHandle.piece_priority(n):
                    print '1',
                else:
                    print '0',

            print '#',

        # Seekpoint
        for n in range(max(self.currentPieceNumber - infoSize, self.filePiecesOffset), min(self.currentPieceNumber + infoSize, self.videoPieces + self.filePiecesOffset - 1)):
            if self.torrentHandle.piece_priority(n):
                print '1',
            else:
                print '0',

        # Footer
        if hasattr(self, 'footerSize') and self.footerSize != 0:
            print '#',
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

        # Tell libtorrent to prioritize this list
        self.torrentHandle.prioritize_pieces(pieceList)

        # Return the list but use a copy otherwise a reference is used which will reflect changes in both ends
        return self.pieces.copy()

    # When header is in, call this function. Start to play movie and enable custom sequential download
    def setHeaderAvailable(self, available):
        self.headerAvailable = available

        from cloudburst.Media.Streamer import Streamer
        Streamer.Instance().setHeaderAvailable(available)

        if self.enableDebugInfo:
            print 'Header available?', available
            self.printTorrentDebug()

    def updatePieceList(self, pieceNumber): # TODO incorporate timer that sets deadlines and increases buffer
        if self.enableDebugInfo:
            print 'Updated piece', pieceNumber

        if pieceNumber in self.pieces:
            if not self.pieces[pieceNumber]:
                self.pieces[pieceNumber] = True

        if not self.headerAvailable:
            if self.isHeaderAvailable():
                self.setHeaderAvailable(True)

    def initializePieces(self):

        # Reset some vars incase of seeking
        self.parent.setDownloadLimit(False)
        self.headerIncreaseSizeCurrent = 0

        # Check cache once, in case the file already existed
        # self.checkCache() # TODO test this works

        # Clear header list incase of seeking an already playing video
        self.pieces.clear()

        # Header pieces
        for n in range(self.filePiecesOffset, self.filePiecesOffset + self.headerSize):
            self.pieces[n] = False                # start of the file

        # Footer size (MKV Cueing data)
        if self.seekPointPieceNumber > self.filePiecesOffset: # footer is only required for seeking # TODO make sure the footer does get downloaded when seeking after playing from 0
            for n in range(0, self.footerSize):
                self.pieces[self.videoPieces + self.filePiecesOffset - 1 - n] = False  # end of the file (MKV needs this) # TODO not needed for avi?

        if self.enableDebugInfo:
            print 'Seekpoint piece:', self.seekPointPieceNumber

        # Make sure the current piece cant go below the first piece of the video
        if self.currentPieceNumber < self.filePiecesOffset:
            self.currentPieceNumber = self.filePiecesOffset



    def threadTorrentInfo(self): # thread

        while not self.torrentHandle.is_seed() and self.isRunning: # while not finished
            self.torrentStatus = self.torrentHandle.status()

            # if self.torrentStatus.progress != 1: # if not finished
            state_str = ['queued', 'checking', 'downloading metadata',
                    'downloading', 'finished', 'seeding', 'allocating', 'checking fastresume']
            print '\rdown: %.1f kB/s, peers: %d, status: %s' % \
                (self.torrentStatus.download_rate / 1000,
                self.torrentStatus.num_peers, state_str[self.torrentStatus.state])

            if self.enableDebugInfo:
                self.printTorrentDebug()

            time.sleep(3)