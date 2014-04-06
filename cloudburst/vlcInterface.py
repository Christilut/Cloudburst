

class VlcInterface:

    videoPosition = 0.0

    def __init__(self, parent, browser):
        self.browser = browser
        self.parent = parent
        self.frame = browser.GetMainFrame()

    def loadVideo(self, jsCallback):
        # jsCallback.Call('file:///D:\\temp\\Frozen.2013.FRENCH.720p.BluRay.x264-ROUGH\\Frozen.2013.FRENCH.720p.BluRay.x264-ROUGH.mkv')
        # jsCallback.Call(self.callback)
        pass

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
        print 'Pos set to:', position
        self.frame.ExecuteJavascript('vlc.input.position = ' + str(position) + ';')

    def getPosition(self):
        return self.videoPosition

    def positionCallback(self, position): # JS calls this #TODO change 100ms timer to VLC event
        # if position != self.videoPosition:
        #     print position

        self.videoPosition = position

    def setTime(self, ms):
        self.frame.ExecuteJavascript('vlc.input.time = ' + str(ms) + ';')

    def changePositionCallback(self, position):
        self.parent.streamingPlayer.setDesiredSeekpoint(position)
