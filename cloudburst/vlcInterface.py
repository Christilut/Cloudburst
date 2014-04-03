

class VlcInterface:
    def __init__(self, browser):
        self.browser = browser

    def loadVideo(self, jsCallback):
        jsCallback.Call('D:\\temp\\Frozen.2013.FRENCH.720p.BluRay.x264-ROUGH\\Frozen.2013.FRENCH.720p.BluRay.x264-ROUGH.mkv')

    def loadVideo2(self):
        self.browser.GetMainFrame().CallFunction('loadAndPlay', 'D:\\temp\\Frozen.2013.FRENCH.720p.BluRay.x264-ROUGH\\Frozen.2013.FRENCH.720p.BluRay.x264-ROUGH.mkv')