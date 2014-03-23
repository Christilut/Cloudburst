import sys
from PyQt4 import QtGui, QtCore
from Lib import libvlc


class Screen(QtGui.QWidget):
    def __init__(self):
        # QtGui.QWidget.__init__(self, master)
        super(Screen, self).__init__()

        self.instance = libvlc.Instance()
        self.mediaplayer = self.instance.media_player_new()

        self.createUI()
        self.isPlaying = False

        # self.PlayPause()

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

        # self.positionslider = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        # self.positionslider.setToolTip("Position")
        # self.positionslider.setMaximum(1000)
        # self.connect(self.positionslider, QtCore.SIGNAL("sliderMoved(int)"), self.setPosition)
        #
        # self.hbuttonbox = QtGui.QHBoxLayout()
        # self.playbutton = QtGui.QPushButton("Play")
        # self.hbuttonbox.addWidget(self.playbutton)
        # self.connect(self.playbutton, QtCore.SIGNAL("clicked()"), self.PlayPause)
        #
        # self.stopbutton = QtGui.QPushButton("Stop")
        # self.hbuttonbox.addWidget(self.stopbutton)
        # self.connect(self.stopbutton, QtCore.SIGNAL("clicked()"), self.Stop)

        # self.hbuttonbox.addStretch(1)
        # self.volumeslider = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        # self.volumeslider.setMaximum(100)
        # self.volumeslider.setValue(self.mediaplayer.audio_get_volume())
        # self.volumeslider.setToolTip("Volume")
        # self.hbuttonbox.addWidget(self.volumeslider)
        # self.connect(self.volumeslider, QtCore.SIGNAL("valueChanged(int)"), self.setVolume)

        self.vboxlayout = QtGui.QVBoxLayout()
        self.vboxlayout.addWidget(self.videoframe)
        # self.vboxlayout.addWidget(self.positionslider)
        # self.vboxlayout.addLayout(self.hbuttonbox)

        self.setLayout(self.vboxlayout)

        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(200) # 200ms
        self.connect(self.timer, QtCore.SIGNAL("timeout()"), self.updateUI)

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

    def PlayPause(self):
        """Toggle play/pause status
        """
        if self.mediaplayer.is_playing():
            self.mediaplayer.pause()
            # self.playbutton.setText("Play")
            self.isPlaying = False
        else:
            if self.mediaplayer.play() == -1:
                self.OpenFile()
                # return
            self.mediaplayer.play()
            # self.playbutton.setText("Pause")
            self.timer.start()
            self.isPlaying = True

    def Stop(self):
        self.mediaplayer.stop()
        self.playbutton.setText("Play")

    def setVolume(self, Volume):
        self.mediaplayer.audio_set_volume(Volume)

    def setPosition(self, position):
        # setting the position to where the slider was dragged
        self.mediaplayer.set_position(position / 1000.0)
        # the vlc MediaPlayer needs a float value between 0 and 1, Qt
        # uses integer variables, so you need a factor; the higher the
        # factor, the more precise are the results
        # (1000 should be enough)

    def updateUI(self):
        # setting the slider to the desired position
        # self.positionslider.setValue(self.mediaplayer.get_position() * 1000)

        if not self.mediaplayer.is_playing():
            # no need to call this function if nothing is played
            self.timer.stop()
            if self.isPlaying:
                # after the video finished, the play button stills shows
                # "Pause", not the desired behavior of a media player
                # this will fix it
                self.Stop()