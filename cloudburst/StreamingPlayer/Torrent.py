import libtorrent as lt
import threading
import time
import appdirs

class Torrent():

    # CONFIG VARS (can edit)
    bufferSize = 5 # in pieces, should be a minimum of paddingSize. Since the peers are lost when the header is available, the buffer needs to be big enough to re-initialize the torrent (around 10 should do) (based on bitrate)
    paddingSize = 3 # when this many pieces are left missing, the buffer is increased
    headerSize = 1 # size of the header (first x pieces)
    footerSize = 1 # size of the footer (last x pieces)

    headerIncreaseSizeAmount = 5 # this many pieces are added to the front AND the back of the header buffer
    headerIncreaseOffset = 1 # if this many pieces are missing from the header, headerIncreaseSizeAmount amount are added. Must be higher than headerIncreaseSizeAmount


    enableDebugInfo = True

    # SYSTEM VARS (do not edit)

    torrentHandle = None
    torrentInfo = None
    torrentStatus = None
    torrentSession = None

    isRunning = False

    videoFileType = None # should be set to MKV, MP4 or AVI, see findVideoFile()

    seekPointPieceNumber = 0 # TODO turn into properties, readonly
    currentPieceNumber = 0
    seekPoint = 0 # from 0 to 1
    videoPieces = -1 # Total amount of pieces in the torrent
    headerAvailable = False
    filePiecesOffset = 0 # Amount of pieces the video file is offset by. These pieces include all skipped files before the video

    headerPiecesAddedToBuffer = False

    totalPieces  = -1 # Total amount of pieces in the torrent

    pieces = {}
    headerPieces = {}
    piecesRequired = 0
    headerPiecesRequired = 0

    headerIncreaseSizeCurrent = 0 # starting value, do not edit # TODO figure out what to do with values that need not be edited

    downloadLimitEnabled = False

    forwardBufferRequested = False
    forwardBufferAvailable = False
    forwardBufferPieces = {}

    downloadDirectory = '' # cant read from appdirs here, set in init

    def __init__(self, parent):

        # Some sanity checks
        assert self.bufferSize >= self.paddingSize
        # TODO add more

        self.isRunning = True

        self.downloadDirectory = appdirs.dirs.user_cache_dir + '\\Download\\'

        # TODO do not remove downloaded torrent but check it instead
        import shutil
        shutil.rmtree(self.downloadDirectory, ignore_errors=True)

        if lt.version != '0.16.16.0':
            print 'Wrong version of libtorrent detected, please install version 0.16.16.0, you have', lt.version
            import sys
            sys.exit(-1)

        self.torrentSession = lt.session()
        self.torrentSession.listen_on(6881, 6882)

        # Allocation settings (these should be default but make sure they are correct)
        settings = lt.session_settings()
        settings.disk_io_write_mode = lt.io_buffer_mode_t.enable_os_cache
        settings.disk_io_read_mode = lt.io_buffer_mode_t.enable_os_cache

        self.torrentSession.set_settings(settings)

        self.parent = parent

    def shutdown(self):
        self.isRunning = False

    # Start the torrent and the required threads
    def startTorrent(self, path, seekpoint = 0):

        self.seekPoint = seekpoint

        if self.torrentHandle is not None:
            print 'Another torrent is already in progress'
            return

        e = lt.bdecode(open(path, 'rb').read())
        self.torrentInfo = lt.torrent_info(e)

        # Print some torrent stats
        if self.enableDebugInfo:
            print 'Torrent piece size:', self.torrentInfo.piece_size(0) / 1024, 'kB'
            print 'Torrent total pieces:', self.torrentInfo.num_pieces()
            print 'Torrent total files:', self.torrentInfo.num_files()

        self.torrentHandle = self.torrentSession.add_torrent({'ti': self.torrentInfo, 'save_path': self.downloadDirectory, 'storage_mode' : lt.storage_mode_t.storage_mode_sparse})

        self.totalPieces = self.torrentInfo.num_pieces()

        videoFile = self.findVideoFile(self.torrentInfo.files())

        self.initializePieces()

        # start download thread
        downloadThread = threading.Thread(target=self.threadTorrentInfo)
        downloadThread.daemon = True
        downloadThread.start()

        # start alert thread
        alertThread = threading.Thread(target=self.threadAlert)
        alertThread.daemon = True
        alertThread.start()

        return self.downloadDirectory + videoFile.path


    # Check which pieces already exist in an existing file, if available
    def checkCache(self):
        for n in iter(self.pieces):
            if self.torrentHandle.have_piece(n):
                if self.pieces[n]:
                    self.updatePieceList(n)

    # Determine which file in the torrent is the video file. Currently based on size and is checked for extension.
    def findVideoFile(self, fileList):
        videoFile = lt.file_entry()
        videoFileIndex = None

        # Currently it is presumed the largest file is the video file. This should be true most of the time.
        for n in range(0, len(fileList)):

            if fileList[n].size > videoFile.size:
                videoFile = fileList[n]
                videoFileIndex = n

        for n in range(0, len(fileList)):
            if not n == videoFileIndex: # dont skip the video file
                self.torrentHandle.file_priority(n, 0);

        piecePriorities = self.torrentHandle.piece_priorities()

        # Count how many pieces are set to 0, these are all the skipped files
        for n in range(0, len(piecePriorities)):

            if piecePriorities[n] == 0:
                self.filePiecesOffset += 1
            else:
                break

        # Now determine how many pieces are in the video file. This is the total amount of pieces in the torrent miuns the pieces of the files before and after the video file
        for n in range(self.filePiecesOffset, len(piecePriorities)):
            if piecePriorities[n] == 1:
                self.videoPieces += 1
            else:
                break

        # Additional check, make sure the file we want (video file) has one of these extensions: .mkv, .avi, .mp4
        splitFileString = str.split(videoFile.path, '.')
        fileExtension = splitFileString[len(splitFileString) - 1]

        if not (fileExtension == 'mkv' or fileExtension == 'avi' or fileExtension == 'mp4'):
            print 'Video file has invalid file extension:', fileExtension
            import sys
            sys.exit(-1) # TODO better way to exit, this doesnt work with CEF

        self.videoFileType = fileExtension.upper()

        return videoFile

    def getBytesDownloaded(self):
        return self.torrentStatus.total_wanted_done

    def getBytesWanted(self):
        return self.torrentStatus.total_wanted

    def printTorrentDebug(self):

        print 'Avail.\t:',

        # Header
        for n in range(self.filePiecesOffset, self.filePiecesOffset + self.headerSize):
            if self.torrentHandle.have_piece(n):
                print '1',
            else:
                print '0',

        print '#',

        # Seekpoint
        for n in range(max(self.seekPointPieceNumber - 50, self.filePiecesOffset), min(self.seekPointPieceNumber + 50, self.videoPieces + self.filePiecesOffset - 1)):
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
        for n in range(max(self.seekPointPieceNumber - 50, self.filePiecesOffset), min(self.seekPointPieceNumber + 50, self.videoPieces + self.filePiecesOffset - 1)):
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

    # Enable the download limit # TODO base it on bitrate
    def setDownloadLimit(self, limited):
        # Set download speed limit (apparently needs to be set after the torrent adding)
        self.downloadLimitEnabled = limited

        if limited:
            downSpeed = 2 * 1024 * 1024
            self.torrentSession.set_download_rate_limit(downSpeed)

            if self.enableDebugInfo:
                print 'Download speed limit set to:', downSpeed / 1024, 'kB/s'
        else:
            print 'Disabled speed limit'
            self.torrentSession.set_download_rate_limit(-1)

    # Sets the torrent to download the video data starting from the seekpoint
    def increaseBuffer(self, missingPieces = None, increasePiecePosition = True):

        # Deadline in ms for normal pieces (not the missing ones)
        pieceDeadlineTime = 5000

        # Increase the buffer, this will be reflected in the priorities
        if increasePiecePosition: # The first time this is called, the current piece should not be moved
            self.currentPieceNumber += self.bufferSize

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
            piece = self.currentPieceNumber + n

            self.pieces[piece] = False # Add to the list
            pieceList[piece] = 1 # Set priority
            self.torrentHandle.set_piece_deadline(piece, pieceDeadlineTime, 1) # Set deadline and enable alert

        # Save the amount of pieces that we currently want
        self.piecesRequired = len(self.pieces)

        # Tell libtorrent to prioritize this list
        self.torrentHandle.prioritize_pieces(pieceList)

        # Return the list but use a copy otherwise a reference is used which will reflect changes in both ends
        return self.pieces.copy()

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
                if missingPieces[n] > self.videoPieces - self.footerSize - 1 or missingPieces[n] < self.headerSize:
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
        self.currentPieceNumber = int(float(self.videoPieces) / 1 * seekpoint) + self.filePiecesOffset
        self.seekPointPieceNumber = self.currentPieceNumber

    # When header is in, call this function. Start to play movie and enable custom sequential download
    def setHeaderAvailable(self, available):
        self.parent.setHeaderAvailable(available)
        self.headerAvailable = available

        if self.enableDebugInfo:
            print 'Header available?', available
            self.printTorrentDebug()

    def isHeaderAvailable(self):
        available = True

        for n in range(self.filePiecesOffset, self.filePiecesOffset + self.headerSize):
            if n in self.headerPieces: # if not in headerPieces, it was set to True and is already removed
                if not self.headerPieces[n]:
                    available = False

        if self.seekPointPieceNumber in self.headerPieces:
            if not self.headerPieces[self.seekPointPieceNumber]:
                available = False

        if self.seekPointPieceNumber != self.filePiecesOffset: # footer does not get added when playing starts from beginning of file (= 0 + filePiecesOffset), so dont check it
            for n in range(self.videoPieces + self.filePiecesOffset - self.footerSize, self.videoPieces + self.filePiecesOffset):
                if n in self.headerPieces: # if not in headerPieces, it was set to True and is already removed
                    if not self.headerPieces[n]:
                        available = False

        return available

    def setForwardBufferAvailable(self):
        self.forwardBufferAvailable = True
        self.parent.forwardBufferAvailable = True

        if not self.downloadLimitEnabled:
            self.setDownloadLimit(True)

        print 'Forward buffer available'

    def isForwardBufferAvailable(self, pieceNumber):

        if pieceNumber in self.forwardBufferPieces:
            self.forwardBufferPieces[pieceNumber] = True

        available = True
        for n in iter(self.forwardBufferPieces):
            if not self.forwardBufferPieces[n]:
                available = False

        return available


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


        if self.parent.canPlay:
            assert self.headerAvailable

        # if header available, the mkv may not yet play. increase the buffer on both ends and keep trying to play.
        if not self.parent.canPlay:

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



    def initializePieces(self):

        # Reset some vars incase of seeking
        self.setDownloadLimit(False)
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
        if self.seekPointPieceNumber > self.filePiecesOffset: # footer is only required for seeking # TODO make sure the footer does get downloaded when seeking after playing from 0
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

    def threadAlert(self):    # Thread. Checks torrent alert messages (like piece ready) and processes them
        pieceTextToFind = 'piece successful' # Libtorrent always reports this when a piece is succesful, with an int attached

        while not self.torrentHandle.is_seed() and self.isRunning:
            if self.torrentSession.wait_for_alert(10) is not None: # None means no alert, timeout
                alert = str(self.torrentSession.pop_alert())

                if pieceTextToFind in alert: # So we extract the int from the text
                    alertSubString = alert.find(pieceTextToFind)
                    pieceNumber = int(alert[alertSubString + len(pieceTextToFind):])

                    # And pass it on to the method that checks pieces
                    self.updatePieceList(pieceNumber) # TODO fix alert spam (has to do with setting deadline on pieces that are already in)

                # print alert # Uncomment this to see all alerts

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

        print self.torrentHandle.name(), 'completed'