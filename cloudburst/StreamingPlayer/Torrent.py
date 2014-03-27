import libtorrent as lt
import threading
import time

class Torrent():

    torrentHandle = None
    torrentInfo = None
    torrentStatus = None
    torrentSession = None

    seekPointPieceNumber = 0
    bufferSize = 20 # in pieces
    seekPoint = 0 # from 0 to 1
    bufferCount = 0

    headerPieces = {}
    dataPieces = {}

    streamState = 'None'

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

        self.SetHeaderPriority()

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

    def SetHeaderPriority(self):
        self.streamState = 'GetHeaderPieces'

        # Check cache once, in case the file already existed
        self.CheckHeaderCache()

        totalPieces = self.torrentInfo.num_pieces()

        # Save prioritized pieces
        self.headerPieces[0] = False                # start of the file
        self.headerPieces[totalPieces - 1] = False  # end of the file (MKV needs this) # TODO not needed for avi?

        self.seekPointPieceNumber = int(float(totalPieces) / 1 * self.seekPoint) - 0 # TODO lower startpiece a bit

        # Set the entire priority list to skip
        pieceList = [0] * totalPieces

        # Save priotitized pieces # TODO determine how large the buffer should be
        for n in range(0, self.bufferSize):
            self.headerPieces[self.seekPointPieceNumber + n] = False

        # Set headers to high priority
        for n in iter(self.headerPieces):
            pieceList[n] = 1
            self.torrentHandle.set_piece_deadline(n, 5000, 1)   # 1 is alert_when_available

        # Set the list to the torrent handle
        self.torrentHandle.prioritize_pieces(pieceList)

    # Sets the torrent to download the video data starting from the seekpoint
    def NextDataPart(self):
        self.streamState = 'GetDataPieces'

        self.bufferCount += 1

        pieceList = [0] * self.torrentInfo.num_pieces()

        for n in range(0, self.bufferSize):
            piece = self.seekPointPieceNumber + self.bufferSize * self.bufferCount + n

            self.dataPieces.clear()
            self.dataPieces[n] = False
            pieceList[piece] = 1
            self.torrentHandle.set_piece_deadline(piece, 5000, 1)

        self.torrentHandle.prioritize_pieces(pieceList)

    def UpdateHeaderProgress(self, piece, available):
        self.headerPieces[piece] = available

        allPiecesAvailable = True
        for n in iter(self.headerPieces):
            if not self.headerPieces[n]:
                allPiecesAvailable = False

        if allPiecesAvailable:
            self.parent.HeaderAvailable(True)

            print 'Header available'

            #TEMP
            print 'Starting sequential data'
            self.torrentHandle.set_sequential_download(True)
            # totalPieces = self.torrentInfo.num_pieces()
            # pieceList = [0] * totalPieces
            # for n in range(self.seekPointPieceNumber, totalPieces - 1):
            #     pieceList[n] = 1

            # self.torrentHandle.prioritize_pieces(pieceList)

            self.NextDataPart() # start the data download, piece by piece

    def UpdateDataProgress(self, piece, available):
        self.dataPieces[piece] = available

        allPiecesAvailable = True
        for n in iter(self.dataPieces):
            if not self.dataPieces[n]:
                allPiecesAvailable = False

        if allPiecesAvailable:
            self.NextDataPart()
            print 'all pieces rdy'

    # Check which pieces already exist in an existing file, if available
    def CheckHeaderCache(self):
        for n in iter(self.headerPieces):
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

    def Alert(self):    # thread
        pieceTextToFind = 'piece successful'

        while True: # TODO while torrent running
            if self.torrentSession.wait_for_alert(100) != 0: # 0 means no alert, timeout
                alert = str(self.torrentSession.pop_alert())

                if pieceTextToFind in alert:
                    alertSubString = alert.find(pieceTextToFind)
                    pieceNumber = int(alert[alertSubString + len(pieceTextToFind):])
                    print 'Got piece', pieceNumber
                    if self.streamState == 'GetHeaderPieces':
                        self.UpdateHeaderProgress(pieceNumber, True)
                    elif self.streamState == 'GetDataPieces':
                        self.UpdateDataProgress(pieceNumber, True)
                    else:
                        print 'Invalid streamState detected'



    def DownloadTorrent(self): # thread
        while (not self.torrentHandle.is_seed()):
            self.torrentStatus = self.torrentHandle.status()

            if self.torrentStatus.progress != 1:
                state_str = ['queued', 'checking', 'downloading metadata',
                        'downloading', 'finished', 'seeding', 'allocating', 'checking fastresume']
                print '\r%.2f%% complete (down: %.1f kB/s, peers: %d) %s' % \
                    (self.torrentStatus.progress * 100, self.torrentStatus.download_rate / 1000,
                    self.torrentStatus.num_peers, state_str[self.torrentStatus.state])

            print 'Avail.\t:',
            for i in range(0, 50):

                if self.torrentHandle.have_piece(i):
                    print '1',
                else:
                    print '0',

            print ''

            print 'Prior.\t:',
            for n in range(0, 50):
                print self.torrentHandle.piece_priority(n),

            print ''


            time.sleep(3)

        print self.torrentHandle.name(), 'completed'