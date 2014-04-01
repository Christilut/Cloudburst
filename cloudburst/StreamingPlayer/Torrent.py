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

    enableDebugInfo = True

    seekPointPieceNumber = 0 # TODO turn into properties, readonly
    currentPieceNumber = 0
    seekPoint = 0 # from 0 to 1
    totalPieces = -1
    headerAvailable = False
    bufferSize = 5 # in pieces, should be a minimum of 3. Since the peers are lost when the header is available, the buffer needs to be big enough to re-initialize the torrent (around 10 should do) (based on bitrate)
    seekPointPreBuffer = 0 #  TODO this value should be based on .. something ? bitrate? i dont know... on mkv container details probably
    seekPointPieceOffset = 0
    headerSize = 1
    footerSize = 1 # TODO fix for size > 1
#TODO if seekpoint = 0, no need for footer
    pieces = {}
    headerPieces = {}
    piecesRequired = 0
    headerPiecesRequired = 0
    piecesPadded = 0

    headerIncreaseSize = 0 # starting value, do not edit # TODO figure out what to do with values that need not be edited
    headerIncreaseSizeAmount = 1 # this many pieces are added to the front AND the back of the header buffer
    headerIncreaseOffset = 1 # if this many pieces are missing from the header, headerIncreaseSizeAmount amount are added. Must be higher than headerIncreaseSizeAmount

    downloadLimitEnabled = False


    def __init__(self, parent):

        if lt.version != '0.16.16.0':
            print 'Wrong version of libtorrent detected, please install version 0.16.16.0, you have', lt.version
            import sys
            sys.exit(-1)

        self.torrentSession = lt.session()
        self.torrentSession.listen_on(6881, 6891)

        # Allocation settings (these should be default but make sure they are correct)
        settings = lt.session_settings()
        settings.disk_io_write_mode = lt.io_buffer_mode_t.enable_os_cache
        settings.disk_io_read_mode = lt.io_buffer_mode_t.enable_os_cache

        self.torrentSession.set_settings(settings)

        self.parent = parent

    def StartTorrent(self, path, seekpoint = 0):

        self.seekPoint = seekpoint

        if self.torrentHandle is not None:
            print 'Another torrent is already in progress'
            return

        e = lt.bdecode(open(path, 'rb').read())
        self.torrentInfo = lt.torrent_info(e)

        self.torrentHandle = self.torrentSession.add_torrent({'ti': self.torrentInfo, 'save_path': 'D:/temp/torrent', 'storage_mode' : lt.storage_mode_t.storage_mode_sparse})

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

    def GetBytesDownloaded(self):
        return self.torrentStatus.total_wanted_done

    def GetBytesWanted(self):
        return self.torrentStatus.total_wanted

    def PrintTorrentDebug(self):
        print 'Avail.\t:',
        for i in range(0, 350):

            if self.torrentHandle.have_piece(i):
                print '1',
            else:
                print '0',

        for n in range(0, self.footerSize):
            if self.torrentHandle.have_piece(self.totalPieces - 1 - n):
                print '1',
            else:
                print '0',

        print ''

        print 'Prior.\t:',
        for n in range(0, 350):
            print self.torrentHandle.piece_priority(n),

        print self.torrentHandle.piece_priority(self.totalPieces - 1),

        print ''

    # Enable the download limit # TODO base it on bitrate
    def EnableDownloadLimit(self):
        # Set download speed limit (apparently needs to be set after the torrent adding)
        self.downloadLimitEnabled = True

        downSpeed = 2 * 1024 * 1024
        self.torrentSession.set_download_rate_limit(downSpeed)

        if self.enableDebugInfo:
            print 'Download speed limit set to:', downSpeed / 1024, 'kB/s'

    # Sets the torrent to download the video data starting from the seekpoint
    def IncreaseBuffer(self, missingPieces = None):

        pieceDeadlineTime = 5000

        self.currentPieceNumber += self.bufferSize

        pieceList = [0] * self.torrentInfo.num_pieces()

        self.pieces.clear()

        if missingPieces != None:

            for n in range(0, len(missingPieces)):

                higherPriority = 2
                pieceDeadlineTime = 2000

                pieceList[missingPieces[n]] = higherPriority # higher priority

                self.pieces[missingPieces[n]] = False
                self.torrentHandle.set_piece_deadline(missingPieces[n], pieceDeadlineTime, 1)

        for n in range(0, self.bufferSize):
            piece = self.currentPieceNumber + n

            self.pieces[piece] = False
            pieceList[piece] = 1 # priority
            self.torrentHandle.set_piece_deadline(piece, pieceDeadlineTime, 1) # set deadline and enable alert

        self.piecesRequired = len(self.pieces)

        self.torrentHandle.prioritize_pieces(pieceList)

    def IncreaseHeader(self, missingPieces = None):

        pieceDeadlineTime = 5000

        self.headerIncreaseSize += 1

        pieceList = [0] * self.torrentInfo.num_pieces()

        self.headerPieces.clear()

        if missingPieces != None:

            for n in range(0, len(missingPieces)):

                higherPriority = 2

                # Make sure header pieces get even higher priority, since the video must wait for these before starting
                if missingPieces[n] == self.totalPieces - 1 or missingPieces[n] == 0: # TODO header/footer may not always be of size 1
                    higherPriority = 3
                    pieceDeadlineTime = 2000

                pieceList[missingPieces[n]] = higherPriority # higher priority

                self.headerPieces[missingPieces[n]] = False
                self.torrentHandle.set_piece_deadline(missingPieces[n], pieceDeadlineTime, 1)


        pieceFront = min(self.currentPieceNumber + self.bufferSize + self.headerIncreaseSize - 1, self.totalPieces - 1) # - 1 because its zero index based
        pieceBack = self.currentPieceNumber - self.headerIncreaseSize

        if pieceFront < self.totalPieces - self.footerSize:
            self.headerPieces[pieceFront] = False # to keep track of availability
            pieceList[pieceFront] = 1 # priority
            self.torrentHandle.set_piece_deadline(pieceFront, pieceDeadlineTime, 1) # set deadline and enable alert

        if pieceBack >= self.headerSize:
            self.headerPieces[pieceBack] = False # to keep track of availability
            pieceList[pieceBack] = 1 # priority
            self.torrentHandle.set_piece_deadline(pieceBack, pieceDeadlineTime, 1) # set deadline and enable alert

        self.headerPiecesRequired = len(self.headerPieces)

        self.torrentHandle.prioritize_pieces(pieceList)

    def SetSeekPoint(self, seekpoint):

        if self.enableDebugInfo:
            print 'Seekpoint set to:', seekpoint

        self.seekPoint = seekpoint

        # Seekpoint position
        self.currentPieceNumber = int(float(self.totalPieces) / 1 * self.seekPoint) - self.seekPointPreBuffer # TODO lower startpiece a bit
        self.seekPointPieceNumber = self.currentPieceNumber

        self.headerAvailable = False

    # When header is in, call this function. Start to play movie and enable custom sequential download
    def SetHeaderAvailable(self):
        self.parent.HeaderAvailable(True)
        self.headerAvailable = True
        print 'Header available'

        if self.enableDebugInfo:
            self.PrintTorrentDebug()

    def IsHeaderAvailable(self):
        available = True
        for n in iter(self.headerPieces):

            if n < self.seekPointPieceNumber + self.bufferSize and not self.headerPieces[n]: # TODO confirm this works properly and/or improve it. bufferSize may not equal header size
                available = False

            if n == self.totalPieces - self.footerSize:   # TODO fix for size > 1
                if not self.headerPieces[self.totalPieces - self.footerSize]:
                    available = False

        return available


    def UpdatePieceList(self, pieceNumber): # TODO incorporate timer that sets deadlines and increases buffer
        if self.enableDebugInfo:
            print 'Updated piece', pieceNumber

        if self.pieces.has_key(pieceNumber):
            self.pieces[pieceNumber] = True # TODO remove instead of setting to true

        if self.headerPieces.has_key(pieceNumber):
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
            if self.IsHeaderAvailable():
                self.SetHeaderAvailable()

        paddingSize = 3 # TODO calculate this
        assert self.bufferSize >= paddingSize

        if self.parent.isPlaying:
            assert self.headerAvailable

        # if header available, the mkv may not yet play. increase the buffer on both ends and keep trying to play.
        if not self.parent.isPlaying:

            if headerPieceAvailableCount >= (self.headerPiecesRequired - self.headerIncreaseOffset):
                missingPieces = []
                for n in iter(self.headerPieces):
                    if not self.headerPieces[n]:
                        missingPieces.append(n)

                self.IncreaseHeader(missingPieces)

        else: # if header + extra pieces large enough (so actually playing), start sequential download
            if not self.downloadLimitEnabled:
                self.EnableDownloadLimit()

            if pieceAvailableCount >= (self.piecesRequired - paddingSize): # x pieces left

                missingPieces = []
                for n in iter(self.pieces):
                    if not self.pieces[n]:
                        missingPieces.append(n)

                # add missing piece as argument so they can be prioritized
                self.IncreaseBuffer(missingPieces)

    def InitializePieces(self):

        # Some value checks
        assert self.seekPointPreBuffer >= 0

        self.totalPieces = self.torrentInfo.num_pieces()

        # Check cache once, in case the file already existed
        self.CheckCache() # TODO test this works

        # Header pieces
        for n in range(0, self.headerSize):
            self.headerPieces[n] = False                # start of the file

        # Footer size (MKV Cueing data)
        for n in range(0, self.footerSize):
            self.headerPieces[self.totalPieces - 1 - n] = False  # end of the file (MKV needs this) # TODO not needed for avi?

        # Seekpoint position
        self.currentPieceNumber = int(float(self.totalPieces) / 1 * self.seekPoint) + self.seekPointPieceOffset
        self.seekPointPieceNumber = self.currentPieceNumber

        if self.enableDebugInfo:
            print 'Seekpoint piece:', self.seekPointPieceNumber

        if self.currentPieceNumber < 0:
            self.currentPieceNumber = 0

        # Set the entire priority list to skip
        pieceList = [0] * self.totalPieces

        # Save priotitized pieces # TODO determine how large the buffer should be
        for n in range(-self.seekPointPreBuffer, self.bufferSize):
            if self.currentPieceNumber + n >= 0:
                self.headerPieces[self.currentPieceNumber + n] = False

        # Save how many we set for later
        self.headerPiecesRequired = len(self.headerPieces)

        # Set headers to high priority
        for n in iter(self.headerPieces):
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

            # if self.torrentStatus.progress != 1:
            state_str = ['queued', 'checking', 'downloading metadata',
                    'downloading', 'finished', 'seeding', 'allocating', 'checking fastresume']
            print '\rdown: %.1f kB/s, peers: %d, status: %s' % \
                (self.torrentStatus.download_rate / 1000,
                self.torrentStatus.num_peers, state_str[self.torrentStatus.state])

            if self.enableDebugInfo:
                self.PrintTorrentDebug()


            time.sleep(3)

        print self.torrentHandle.name(), 'completed'