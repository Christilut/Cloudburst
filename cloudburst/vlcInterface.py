import time
from cloudburst.util.Singleton import Singleton
# from cloudburst.StreamingPlayer.StreamingPlayer import StreamingPlayer

@Singleton
class VlcInterface: # TODO make static
# TODO replace with jsBinding properties

    frame = None
    browser = None

    videoLength = -1 # in ms
    videoLengthReceived = False # workaround for the async js operation

    videoPosition = 0.0
    videoPositionReceived = False

    videoCurrentTime = 0
    videoCurrentTimeReceived = False

    def __init__(self):
        pass

    def setBrowser(self, browser):
        self.browser = browser
        self.frame = browser.GetMainFrame()

    def openFile(self, path):
        fullPath = 'file:///' + path
        self.frame.CallFunction('openFile', fullPath)

        # self.frame.ExecuteJavascript('var vlc = document.getElementById(\"vlc\");' # TODO cant get this to work
        #                              'vlc.playlist.items.clear();'
        #                              'var options = new Array(\":aspect-ratio=4:3\", \"--rtsp-tcp\");'
        #                              'fileID = vlc.playlist.add(\"' + fullPath + '\", \"fancy name\", options);')

    def play(self): # TODO check which of these functions is actually used by the back end
        self.frame.ExecuteJavascript('vlc.playlist.playItem(fileID);')

    def pause(self):
        self.frame.ExecuteJavascript('vlc.playlist.pause();')

    def playPause(self):
        self.frame.ExecuteJavascript('vlc.playlist.togglePause();')

    def stop(self):
        self.frame.ExecuteJavascript('vlc.playlist.stop();')

    def setPosition(self, position):
        print 'Position set to:', position
        self.frame.ExecuteJavascript('vlc.input.position = ' + str(position) + ';')

    def getPosition(self):
        self.frame.ExecuteJavascript('javascript:python.videoPositionCallback(vlc.input.position)')

        timeWaiting = 0
        while not self.videoPositionReceived and timeWaiting < 10: # hacky but tests show it takes ~1ms during no load situations
            time.sleep(0.001)

        self.videoPositionReceived = False

        if timeWaiting >= 10:
            print 'Error! Could not get the video position from VLC'
            return -1
        print self.videoPosition
        return self.videoPosition

    def videoPositionCallback(self, position): # JS calls this, cant be static
        self.videoPosition = position
        self.videoPositionReceived = True

    def getVideoLength(self): # TODO can this be less hacky?
        self.frame.ExecuteJavascript('javascript:python.videoLengthCallback(vlc.input.length)')

        timeWaiting = 0
        while not self.videoLengthReceived and timeWaiting < 10: # hacky but tests show it takes ~1ms during no load situations
            time.sleep(0.001)

        self.videoLengthReceived = False

        if timeWaiting >= 10:
            print 'Error! Could not get the video length from VLC'
            return -1
        # print self.videoLength
        return self.videoLength

    def videoLengthCallback(self, length):
        self.videoLength = length
        self.videoLengthReceived = True

    def getTime(self):
        self.frame.ExecuteJavascript('javascript:python.videoCurrentTimeCallback(vlc.input.time)')

        timeWaiting = 0
        while not self.videoCurrentTimeReceived and timeWaiting < 10: # hacky but tests show it takes ~1ms during no load situations
            time.sleep(0.001)

        self.videoCurrentTimeReceived = False

        if timeWaiting >= 10:
            print 'Error! Could not get the video position from VLC'
            return -1

        return self.videoCurrentTime

    def videoCurrentTimeCallback(self, time): # JS calls this, cant be static
        self.videoCurrentTime = time
        self.videoCurrentTimeReceived = True

    def setTime(self, ms):
        self.frame.ExecuteJavascript('vlc.input.time = ' + str(ms) + ';')

    def changePositionCallback(self, position):
        from cloudburst.StreamingPlayer.StreamingPlayer import StreamingPlayer # cant call it at the top
        StreamingPlayer.Instance().setDesiredSeekpoint(position)