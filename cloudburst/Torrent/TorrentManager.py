from libtorrent import file_storage
import libtorrent as lt
import threading
import time
import shutil

class TorrentManager():

    torrentHandle = None

    def __init__(self):
        self.session = lt.session()
        self.session.listen_on(6881, 6891)

        # TEMP REMOVE DOWNLOADED TORRENT
        shutil.rmtree('D:/temp/torrent', ignore_errors=True)

    def StartTorrent(self, path):

        if self.torrentHandle is not None:
            print 'Another torrent is already in progress'
            return

        e = lt.bdecode(open(path, 'rb').read())
        info = lt.torrent_info(e)

        self.torrentHandle = self.session.add_torrent({'ti': info, 'save_path': 'D:/temp/torrent'})
        self.torrentHandle.set_sequential_download(True)

        videoFile = self.FindVideoFile(info.files())

        downloadThread = threading.Thread(target=self.DownloadTorrent)
        downloadThread.daemon = True
        downloadThread.start()

        return videoFile.path

    def FindVideoFile(self, fileList):

        videoFile = lt.file_entry()

        # Currently it is presumed the largest file is the video file. This should be true most of the time.
        for f in fileList:
            if f.size > videoFile.size:
                videoFile = f

        return videoFile

    def DownloadTorrent(self):

        while (not self.torrentHandle.is_seed()):
            torrentStatus = self.torrentHandle.status()

            state_str = ['queued', 'checking', 'downloading metadata',
                    'downloading', 'finished', 'seeding', 'allocating', 'checking fastresume']
            print '\r%.2f%% complete (down: %.1f kb/s up: %.1f kB/s peers: %d) %s' % \
                (torrentStatus.progress * 100, torrentStatus.download_rate / 1000,
                 torrentStatus.upload_rate / 1000,
                torrentStatus.num_peers, state_str[torrentStatus.state])

            # check if file exists, so we can start the stream


            time.sleep(1)

        print self.torrentHandle.name(), 'completed'