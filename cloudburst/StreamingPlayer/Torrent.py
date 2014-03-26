import libtorrent as lt
import threading
import time

class Torrent():

    torrentHandle = None
    torrentInfo = None
    torrentStatus = None

    def __init__(self):
        self.session = lt.session()
        self.session.listen_on(6881, 6891)

    def StartTorrent(self, path):

        if self.torrentHandle is not None:
            print 'Another torrent is already in progress'
            return

        e = lt.bdecode(open(path, 'rb').read())
        self.torrentInfo = lt.torrent_info(e)

        self.torrentHandle = self.session.add_torrent({'ti': self.torrentInfo, 'save_path': 'D:/temp/torrent', 'storage_mode' : lt.storage_mode_t.storage_mode_sparse})
        self.torrentHandle.set_sequential_download(True)

        videoFile = self.FindVideoFile(self.torrentInfo.files())
        self.SetTorrentProgress(90) #TEMP
        downloadThread = threading.Thread(target=self.DownloadTorrent)
        downloadThread.daemon = True
        downloadThread.start()

        return videoFile.path

    def SetTorrentProgress(self, percentage): # Set the torrent to download from this point in percentage TODO use progress

        totalPieces = self.torrentInfo.num_pieces()
        startPiece = int(float(totalPieces) / 100 * percentage)

        pieceList = []

        for i in range(0, 50):
            pieceList.append(1)

        for i in range(50, 839):
            pieceList.append(0)

        for i in range(839, 939):
            pieceList.append(1)

        # First add priority 0 to all pieces before the start piece, these are not downloaded
        for i in range(939, startPiece):
            pieceList.append(0)

        # Now add the pieces after the start piece to normal priority
        for i in range(startPiece, totalPieces):
            pieceList.append(1)

        # Set the list to the torrent handle
        self.torrentHandle.prioritize_pieces(pieceList)

        self.torrentHandle.set_sequential_download(True)


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

    def DownloadTorrent(self): # thread
        while (not self.torrentHandle.is_seed()):
            self.torrentStatus = self.torrentHandle.status()

            state_str = ['queued', 'checking', 'downloading metadata',
                    'downloading', 'finished', 'seeding', 'allocating', 'checking fastresume']
            print '\r%.2f%% complete (down: %.1f kB/s, peers: %d) %s' % \
                (self.torrentStatus.progress * 100, self.torrentStatus.download_rate / 1000,
                self.torrentStatus.num_peers, state_str[self.torrentStatus.state])

            pieceTotal = self.torrentInfo.num_pieces()
            # for i in range(0, pieceTotal):
            #     print self.torrentHandle.have_piece(i),

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