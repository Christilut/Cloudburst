class VlcInterface:
    def __init__(self, browser):
        self.browser = browser

    def loadVideo(self, jsCallback):
        jsCallback.Call('file:///res/vids/big-buck-bunny_trailer.webm')