import sys
from PyQt4 import QtGui, QtCore
import libvlc


class ScreenVLC(QtGui.QWidget):
    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)

        self.parent = parent

        self.resize(parent.size())
        self.instance = libvlc.Instance()
        self.mediaplayer = self.instance.media_player_new()

        self.createUI()

    def createUI(self):
        # self.widget = QtGui.QWidget(self)

        # In this widget, the video will be drawn
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



    def OpenFile(self):
        # create the media
        self.media = self.instance.media_new('D:\\temp\\test.mkv')
        # put the media in the media player
        self.mediaplayer.set_media(self.media)

        # parse the metadata of the file
        self.media.parse()
        # set the title of the track as window title
        self.setWindowTitle(self.media.get_meta(0))

        if sys.platform == "linux2": # for Linux using the X Server
            self.mediaplayer.set_xwindow(self.videoframe.winId())
        elif sys.platform == "win32": # for Windows
            self.mediaplayer.set_hwnd(self.videoframe.winId())
        elif sys.platform == "darwin": # for MacOS
            self.mediaplayer.set_nsobject(self.videoframe.winId())
        self.mediaplayer.play()


    def Play(self):
        if not self.mediaplayer.is_playing():
            if self.mediaplayer.get_media() == None:
                self.OpenFile()

            self.mediaplayer.play()

    def Pause(self):
        if self.mediaplayer.is_playing():
            self.mediaplayer.pause()

    def Stop(self):
        self.mediaplayer.stop()

    def setVolume(self, Volume):
        self.mediaplayer.audio_set_volume(Volume)

    def setPosition(self, position):
        # setting the position to where the slider was dragged
        self.mediaplayer.set_position(position / 1000.0)
        # the vlc MediaPlayer needs a float value between 0 and 1, Qt
        # uses integer variables, so you need a factor; the higher the
        # factor, the more precise are the results
        # (1000 should be enough)

