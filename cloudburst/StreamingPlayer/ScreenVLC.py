import sys
from PyQt4 import QtGui
import libvlc


class ScreenVLC(QtGui.QWidget):
    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)

        self.parent = parent

        self.resize(parent.size())
        self.instance = libvlc.Instance()
        self.mediaplayer = self.instance.media_player_new()

        self.mediaplayer.video_set_mouse_input(True)

        self.createUI()

    def createUI(self):

        if sys.platform == "darwin": # for MacOS
            self.videoframe = QtGui.QMacCocoaViewContainer(0)
        else:
            self.videoframe = QtGui.QFrame()
        self.palette = self.videoframe.palette()
        self.palette.setColor (QtGui.QPalette.Window, QtGui.QColor(0,0,0))
        self.videoframe.setPalette(self.palette)
        self.videoframe.setAutoFillBackground(True)

        self.vboxlayout = QtGui.QVBoxLayout()
        self.vboxlayout.setContentsMargins(0, 0, 0, 0)
        self.vboxlayout.addWidget(self.videoframe)
        self.setLayout(self.vboxlayout)

    def OpenFile(self, path):
        # create the media
        self.media = self.instance.media_new(path)
        # put the media in the media player
        self.mediaplayer.set_media(self.media)

        # parse the metadata of the file
        self.media.parse()
        # set the title of the track as window title
        # self.setWindowTitle(self.media.get_meta(0))

        if sys.platform == "linux2": # for Linux using the X Server
            self.mediaplayer.set_xwindow(self.videoframe.winId())
        elif sys.platform == "win32": # for Windows
            self.mediaplayer.set_hwnd(self.videoframe.winId())
        elif sys.platform == "darwin": # for MacOS
            self.mediaplayer.set_nsobject(self.videoframe.winId())


    def Play(self, position = -1):  # from 0 to 1
        if not self.mediaplayer.is_playing():
            self.mediaplayer.play()

            if position != -1:
                self.mediaplayer.set_position(position)

    def Pause(self):
        if self.mediaplayer.is_playing():
            self.mediaplayer.pause()

    def Stop(self):
        self.mediaplayer.stop()

    def setVolume(self, Volume):
        self.mediaplayer.audio_set_volume(Volume)

