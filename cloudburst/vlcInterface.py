import time

class VlcInterface: # TODO make static
# TODO replace with jsBinding properties

    videoLength = -1 # in ms
    videoLengthReceived = False # workaround for the async js operation

    videoPosition = 0.0
    videoPositionReceived = False

    def __init__(self, parent, browser, jsbindings):
        self.browser = browser
        self.parent = parent
        self.jsBindings = jsbindings
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

        while not self.videoPositionReceived: # hacky but tests show it takes ~1ms during no load situations
            time.sleep(0.001)

        self.videoPositionReceived = False

        return self.videoPosition

    def videoPositionCallback(self, position): # JS calls this
        self.videoPosition = position
        self.videoPositionReceived = True

    def getVideoLength(self): # TODO can this be less hacky?
        self.frame.ExecuteJavascript('javascript:python.videoLengthCallback(vlc.input.length)')

        while not self.videoLengthReceived: # hacky but tests show it takes ~1ms during no load situations
            time.sleep(0.001)

        self.videoLengthReceived = False

        return self.videoLength

    def videoLengthCallback(self, length):
        self.videoLength = length
        self.videoLengthReceived = True

    def setTime(self, ms):
        self.frame.ExecuteJavascript('vlc.input.time = ' + str(ms) + ';')

    def changePositionCallback(self, position):
        self.parent.streamingPlayer.setDesiredSeekpoint(position)

    def test(self):
        #self.jsBindings.SetProperty('testProperty', 'hello')

        self.frame.ExecuteJavascript('test()')
