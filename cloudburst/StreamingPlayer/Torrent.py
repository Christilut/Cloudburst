import libtorrent as lt
import threading
import time

class Torrent():

    torrentHandle = None
    torrentInfo = None
    torrentStatus = None
    torrentSession = None

    headerPieces = {}
    seekPointPieces = {}

    streamState = 'None'

    def __init__(self, parent):
        self.torrentSession = lt.session()
        self.torrentSession.listen_on(6881, 6891)

        self.parent = parent

    def StartTorrent(self, path):

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

        totalPieces = self.torrentInfo.num_pieces()

        # Save prioritized pieces
        self.headerPieces[0] = False                # start of the file
        self.headerPieces[totalPieces - 1] = False  # end of the file (MKV needs this) # TODO not needed for avi?

        # Set the entire priority list to skip
        pieceList = [0] * totalPieces

        # Set headers to high priority
        for n in iter(self.headerPieces):
            pieceList[n] = 7
            self.torrentHandle.set_piece_deadline(n, 1000, 1)   # 1 is alert_when_available

        # Set the list to the torrent handle
        self.torrentHandle.prioritize_pieces(pieceList)

    def SetSeekPointPriority(self, seekpoint): # Set the torrent to download from this point in percentage
        self.streamState = 'GetSeekPointPieces'

        totalPieces = self.torrentInfo.num_pieces()
        startPiece = int(float(totalPieces) / 1 * seekpoint) - 0 # TODO lower startpiece a bit

        # Save priotitized pieces # TODO determine how large the buffer should be
        for n in range(0, 3):
            self.seekPointPieces[startPiece + n] = False

        # Set the entire priority list to skip
        pieceList = [0] * totalPieces

        # Enable pieces
        for n in iter(self.seekPointPieces):
            pieceList[n] = 1
            self.torrentHandle.set_piece_deadline(n, 1000, 1)   # 1 is alert_when_available

        # Set the list to the torrent handle
        self.torrentHandle.prioritize_pieces(pieceList)

    # Sets the torrent to download the video data starting from the seekpoint
    def SetDataPriority(self, seekpoint):
        self.streamState = 'GetDataPieces'

        # Time to enable sequential download, since we stream after this
        self.torrentHandle.set_sequential_download(True)

        totalPieces = self.torrentInfo.num_pieces()
        startPiece = int(float(totalPieces) / 1 * seekpoint)

        # TODO keep track of pieces so it can be seen in advance if the download speed is lacking

        # Set the entire priority list to skip
        pieceList = [0] * totalPieces

        for n in range(startPiece, totalPieces):
            pieceList[n] = 1

        # Set the list to the torrent handle
        self.torrentHandle.prioritize_pieces(pieceList)

    def UpdateHeaderProgress(self, piece, available):
        self.headerPieces[piece] = available

        allPiecesAvailable = True
        for n in iter(self.headerPieces):
            allPiecesAvailable = self.headerPieces[n]

        if allPiecesAvailable:
            self.parent.HeaderAvailable(True)

    def UpdateSeekPointProgress(self, piece, available):
        self.seekPointPieces[piece] = available

        allPiecesAvailable = True
        for n in iter(self.seekPointPieces):
            allPiecesAvailable = self.seekPointPieces[n]

        if allPiecesAvailable:
            self.parent.SeekPointAvailable(True)

    # Check which pieces already exist in an existing file, if available
    def CheckHeaderCache(self):
        for n in iter(self.headerPieces):
            if self.torrentHandle.have_piece(n):
                self.UpdateHeaderProgress(n, True)  # ignore False state

    def CheckSeekPointCache(self):
        for n in iter(self.seekPointPieces):
            if self.torrentHandle.have_piece(n):
                self.UpdateSeekPointProgress(n, True)  # ignore False state

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
            if self.torrentSession.wait_for_alert(1000) != 0: # 0 means no alert, timeout
                alert = str(self.torrentSession.pop_alert())

                if pieceTextToFind in alert:
                    alertSubString = alert.find(pieceTextToFind)
                    pieceNumber = int(alert[alertSubString + len(pieceTextToFind):])

                    if self.streamState == 'GetHeaderPieces':
                        self.UpdateHeaderProgress(pieceNumber, True)
                    elif self.streamState == 'GetSeekPointPieces':
                        self.UpdateSeekPointProgress(pieceNumber, True)
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

            pieceTotal = self.torrentInfo.num_pieces()
            foundPiece = False
            for i in range(0, pieceTotal):

                if(not foundPiece):
                    if(self.torrentHandle.have_piece(i)):
                        print i, ' True    |   ',
                        foundPiece = True
                else:
                    if(not self.torrentHandle.have_piece(i)):
                        print i, ' False   |   ',
                        foundPiece = False

            print ''


            time.sleep(1)

        print self.torrentHandle.name(), 'completed'