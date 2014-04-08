import libtorrent as lt
from MKVTorrent import MKVTorrent
from MP4Torrent import MP4Torrent
from AVITorrent import AVITorrent
import appdirs, threading

class TorrentManager():

    torrent = None
    torrentHandle = None
    torrentSession = None

    isRunning = False

    videoFile = lt.file_entry()

    def __init__(self, parent):

        self.parent = parent

        if lt.version != '0.16.16.0':
            print 'Wrong version of libtorrent detected, please install version 0.16.16.0, you have', lt.version
            import sys
            sys.exit(-1)

        self.downloadDirectory = appdirs.dirs.user_cache_dir + '\\Download\\'

        # TODO do not remove downloaded torrent but check it instead
        import shutil
        shutil.rmtree(self.downloadDirectory, ignore_errors=True)

        self.isRunning = True

    def shutdown(self):
        self.isRunning = False
        self.torrent.shutdown()

    def diskSpaceCheck(self): # TODO
        pass

    def setHeaderAvailable(self, available):
        self.parent.setHeaderAvailable(available)

    def startTorrent(self):
        self.torrent.startTorrent()

    def openTorrent(self, path, seekpoint = 0):

        if self.torrentHandle is not None:
            print 'Another torrent is already in progress'
            return

        self.torrentSession = lt.session()
        self.torrentSession.listen_on(6881, 6891)

        # Allocation settings (these should be default but make sure they are correct)
        settings = lt.session_settings()
        settings.close_redundant_connections = False # This keeps peers connected
        settings.disk_io_write_mode = lt.io_buffer_mode_t.enable_os_cache
        settings.disk_io_read_mode = lt.io_buffer_mode_t.enable_os_cache

        self.torrentSession.set_settings(settings)

        e = lt.bdecode(open(path, 'rb').read())
        torrentInfo = lt.torrent_info(e)

        self.torrentHandle = self.torrentSession.add_torrent({'ti': torrentInfo, 'save_path': self.downloadDirectory, 'storage_mode' : lt.storage_mode_t.storage_mode_sparse})

        self.videoFile = self.findVideoFile(torrentInfo.files())

        # Disable all files, we do not want to download yet. Download starts when torrent.startTorrent() is called
        # for n in range(0, torrentInfo.num_files()):
        filesSkipped = [0] * torrentInfo.num_files()
        self.torrentHandle.prioritize_files(filesSkipped)

        # Print some torrent stats
        print 'Torrent piece size:', torrentInfo.piece_size(0) / 1024, 'kB'
        print 'Torrent total pieces:', torrentInfo.num_pieces()
        print 'Torrent total files:', torrentInfo.num_files()
        print 'Video file offset pieces:', self.filePiecesOffset

        if self.videoFileType == 'MKV':
            self.torrent = MKVTorrent(self, self.torrentHandle)
        elif self.videoFileType == 'MP4':
            self.torrent = MP4Torrent(self, self.torrentHandle)
        elif self.videoFileType == 'AVI':
            self.torrent = AVITorrent(self, self.torrentHandle)

        totalPieces = torrentInfo.num_pieces()

        self.torrent.openTorrent(seekpoint, totalPieces, self.videoPieces, self.filePiecesOffset)

        # start alert thread
        alertThread = threading.Thread(target=self.threadAlert)
        alertThread.daemon = True
        alertThread.start()

        return self.downloadDirectory + self.videoFile.path


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
        self.filePiecesOffset = 0
        for n in range(0, len(piecePriorities)):

            if piecePriorities[n] == 0:
                self.filePiecesOffset += 1
            else:
                break

        # Now determine how many pieces are in the video file. This is the total amount of pieces in the torrent miuns the pieces of the files before and after the video file
        self.videoPieces = 0
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

        print 'Torrent configured for file type:', self.videoFileType

        return videoFile

    # Enable the download limit # TODO base it on bitrate
    def setDownloadLimit(self, limited):
        # Set download speed limit (apparently needs to be set after the torrent adding)
        self.downloadLimitEnabled = limited

        if limited:

            videoFileSize = float(self.videoFile.size) # in bytes
            videoFileLength = float(self.parent.getVideoLength()) / 1000 # in s

            if videoFileLength > 0: # VLC may report -1 or 0 if it cant find the file length (seems to happen on AVI's)

                downSpeed = videoFileSize / videoFileLength

                # add speed to be sure
                downSpeed *= 1.5

            else: # incase of no known length, set it to a default of 2MBps
                downSpeed = 2 * 1024 * 1024

            self.torrentSession.set_download_rate_limit(int(downSpeed))
            print 'Download speed limit set to:', int(downSpeed) / 1024, 'kB/s'

        else:
            print 'Disabled speed limit'
            self.torrentSession.set_download_rate_limit(-1)




    def threadAlert(self):    # Thread. Checks torrent alert messages (like piece ready) and processes them
        pieceTextToFind = 'piece successful' # Libtorrent always reports this when a piece is succesful, with an int attached

        while not self.torrentHandle.is_seed() and self.isRunning:
            if self.torrentSession.wait_for_alert(10) is not None: # None means no alert, timeout
                alert = str(self.torrentSession.pop_alert())

                if pieceTextToFind in alert: # So we extract the int from the text
                    alertSubString = alert.find(pieceTextToFind)
                    pieceNumber = int(alert[alertSubString + len(pieceTextToFind):])

                    # And pass it on to the method that checks pieces
                    self.torrent.updatePieceList(pieceNumber) # TODO fix alert spam (has to do with setting deadline on pieces that are already in)

                # print alert # Uncomment this to see all alerts