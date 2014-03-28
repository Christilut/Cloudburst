import libtorrent as lt
import threading
import time

class Piece():
    def __init__(self, parent):
        self.parent = parent

class Torrent():

    torrentHandle = None
    torrentInfo = None
    torrentStatus = None
    torrentSession = None

    seekPointPieceNumber = 0
    currentPieceNumber = 0
    bufferSize = 3 # in pieces
    seekPoint = 0 # from 0 to 1
    totalPieces = -1
    headerAvailable = False

    pieces = {}
    piecesRequired = 0
    piecesPadded = 0


    def __init__(self, parent):
        self.torrentSession = lt.session()
        self.torrentSession.listen_on(6881, 6891)

        self.parent = parent

    def StartTorrent(self, path, seekpoint = 0):

        self.seekPoint = seekpoint

        if self.torrentHandle is not None:
            print 'Another torrent is already in progress'
            return

        e = lt.bdecode(open(path, 'rb').read())
        self.torrentInfo = lt.torrent_info(e)

        self.torrentHandle = self.torrentSession.add_torrent({'ti': self.torrentInfo, 'save_path': 'D:/temp/torrent', 'storage_mode' : lt.storage_mode_t.storage_mode_sparse})

        # Set download speed limit
        self.torrentSession.set_download_rate_limit(2 * 1024 * 1024) # TODO calculate required speed based on VLC reported bitrate

        videoFile = self.FindVideoFile(self.torrentInfo.files())

        # start download thread
        downloadThread = threading.Thread(target=self.DownloadTorrent)
        downloadThread.daemon = True
        downloadThread.start()

        # start alert thread
        alertThread = threading.Thread(target=self.Alert)
        alertThread.daemon = True
        alertThread.start()

        return videoFile.path


    # Check which pieces already exist in an existing file, if available
    def CheckCache(self):
        for n in iter(self.pieces):
            if self.torrentHandle.have_piece(n):
                self.UpdateHeaderProgress(n, True)  # ignore False state

    def FindVideoFile(self, fileList):
        videoFile = lt.file_entry()

        # Currently it is presumed the largest file is the video file. This should be true most of the time.
        # TODO find better way to determine which file is the video, file extension?
        # TODO skip files that are not video
        for f in fileList:
            if f.size > videoFile.size:
                videoFile = f

        return videoFile

    def getBytesDownloaded(self):
        return self.torrentStatus.total_wanted_done

    def getBytesWanted(self):
        return self.torrentStatus.total_wanted

    def PrintTorrentDebug(self):
        print 'Avail.\t:',
        for i in range(0, 100):

            if self.torrentHandle.have_piece(i):
                print '1',
            else:
                print '0',

        if self.torrentHandle.have_piece(self.totalPieces - 1):
            print '1',
        else:
            print '0',

        print ''

        print 'Prior.\t:',
        for n in range(0, 100):
            print self.torrentHandle.piece_priority(n),

        print self.torrentHandle.piece_priority(self.totalPieces - 1),

        print ''

    # Sets the torrent to download the video data starting from the seekpoint
    def IncreaseBuffer(self, missingPieces = None):

        self.currentPieceNumber += self.bufferSize

        pieceList = [0] * self.torrentInfo.num_pieces()

        self.pieces.clear()

        if missingPieces != None:

            for n in range(0, len(missingPieces)):

                higherPriority = 2
                deadlineTime = 2000 # in ms

                # Make sure header pieces get even higher priority, since the video must wait for these before starting
                if missingPieces[n] == self.totalPieces - 1 or missingPieces[n] == 0: # TODO header/footer may not always be 1
                    higherPriority = 7
                    deadlineTime = 5000

                pieceList[missingPieces[n]] = higherPriority # higher priority

                self.pieces[missingPieces[n]] = False
                self.torrentHandle.set_piece_deadline(missingPieces[n], deadlineTime, 1)

        for n in range(0, self.bufferSize):
            piece = self.currentPieceNumber + n

            self.pieces[piece] = False
            pieceList[piece] = 1
            self.torrentHandle.set_piece_deadline(piece, 5000, 1)

        self.piecesRequired = len(self.pieces)

        self.torrentHandle.prioritize_pieces(pieceList)


    def IsHeaderAvailable(self):

        available = True
        for n in iter(self.pieces):

            if n < self.seekPointPieceNumber + self.bufferSize and not self.pieces[n]: # TODO confirm this works properly and/or improve it. bufferSize may not equal header size
                available = False

            if n == self.totalPieces - 1: # TODO assuming end header is 1 piece
                if not self.pieces[self.totalPieces - 1]:
                    available = False

        return available


    def UpdatePieceList(self, pieceNumber): # TODO incorporate timer that sets deadlines and increases buffer
        # print 'Updated piece', pieceNumber
        self.pieces[pieceNumber] = True

        pieceAvailableCount = 0
        for n in iter(self.pieces):
            if self.pieces[n]:
                pieceAvailableCount += 1

        if not self.headerAvailable:
            if self.IsHeaderAvailable():
                self.parent.HeaderAvailable(True)
                self.headerAvailable = True
                print 'Header available'
                # self.PrintTorrentDebug()

        paddingSize = 3 # TODO calculate this
        assert self.bufferSize >= paddingSize

        if pieceAvailableCount == (self.piecesRequired - paddingSize): # x pieces left

            missingPieces = []
            for n in iter(self.pieces):
                if not self.pieces[n]:
                    missingPieces.append(n)

            # add missing piece as argument so they can be prioritized
            self.IncreaseBuffer(missingPieces)

    def InitializePieces(self):

        self.totalPieces = self.torrentInfo.num_pieces()

        # Check cache once, in case the file already existed
        self.CheckCache()

        # Header pieces
        self.pieces[0] = False                # start of the file
        self.pieces[self.totalPieces - 1] = False  # end of the file (MKV needs this) # TODO not needed for avi?

        # Seekpoint position
        self.currentPieceNumber = int(float(self.totalPieces) / 1 * self.seekPoint) - 1 # TODO lower startpiece a bit
        self.seekPointPieceNumber = self.currentPieceNumber

        if self.currentPieceNumber < 0:
            self.currentPieceNumber = 0

        # Set the entire priority list to skip
        pieceList = [0] * self.totalPieces

        # Save priotitized pieces # TODO determine how large the buffer should be
        for n in range(0, self.bufferSize):
            self.pieces[self.currentPieceNumber + n] = False

        # Save how many we set for later
        self.piecesRequired = len(self.pieces)

        # Set headers to high priority
        for n in iter(self.pieces):
            pieceList[n] = 1
            self.torrentHandle.set_piece_deadline(n, 5000, 1)   # 1 is alert_when_available

        # Set the list to the torrent handle
        self.torrentHandle.prioritize_pieces(pieceList)

    def Alert(self):    # thread
        pieceTextToFind = 'piece successful'

        while True: # TODO while torrent running
            if self.torrentSession.wait_for_alert(10) != None: # None means no alert, timeout
                alert = str(self.torrentSession.pop_alert())

                if pieceTextToFind in alert:
                    alertSubString = alert.find(pieceTextToFind)
                    pieceNumber = int(alert[alertSubString + len(pieceTextToFind):])
                    # print 'Got piece', pieceNumber

                    self.UpdatePieceList(pieceNumber)
                # else:
                #     print alert

    def DownloadTorrent(self): # thread

        self.InitializePieces()

        while (not self.torrentHandle.is_seed()):
            self.torrentStatus = self.torrentHandle.status()

            if self.torrentStatus.progress != 1:
                state_str = ['queued', 'checking', 'downloading metadata',
                        'downloading', 'finished', 'seeding', 'allocating', 'checking fastresume']
                print '\rdown: %.1f kB/s, peers: %d, status: %s' % \
                    (self.torrentStatus.download_rate / 1000,
                    self.torrentStatus.num_peers, state_str[self.torrentStatus.state])


                # self.PrintTorrentDebug()


            time.sleep(3)

        print self.torrentHandle.name(), 'completed'