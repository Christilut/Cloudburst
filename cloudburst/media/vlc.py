import time
from singleton.singleton import Singleton


@Singleton
class VLC:
    # TODO replace with jsBinding properties

    frame = None
    browser = None

    video_length = -1                    # in ms
    video_length_received = False         # workaround for the async js operation

    video_position = 0.0                 # from 0 to 1
    video_position_received = False       # workaround

    video_current_time = 0                # in ms
    video_current_time_received = False    # workaround

    def __init__(self):
        pass

    def set_browser(self, browser):      # TODO put in init
        self.browser = browser
        self.frame = browser.GetMainFrame()

    def open_file(self, path):
        fullpath = 'file:///' + path
        self.frame.CallFunction('openFile', fullpath)

        # self.frame.ExecuteJavascript('var vlc = document.getElementById(\"vlc\");' # TODO cant get this to work
        #                              'vlc.playlist.items.clear();'
        #                              'var options = new Array(\":aspect-ratio=4:3\", \"--rtsp-tcp\");'
        #                              'fileID = vlc.playlist.add(\"' + fullPath + '\", \"fancy name\", options);')

    def play(self):     # TODO check which of these functions is actually used by the back end
        self.frame.ExecuteJavascript('vlc.playlist.playItem(fileID);')

    def pause(self):
        self.frame.ExecuteJavascript('vlc.playlist.pause();')

    def play_pause(self):
        self.frame.ExecuteJavascript('vlc.playlist.togglePause();')

    def stop(self):
        self.frame.ExecuteJavascript('vlc.playlist.stop();')

    def set_position(self, position):
        print 'Position set to:', position
        self.frame.ExecuteJavascript('vlc.input.position = ' + str(position) + ';')

    def get_video_position(self):
        self.frame.ExecuteJavascript('javascript:python.video_position_callback(vlc.input.position)')

        t = 0
        while not self.video_position_received and t < 10:        # hacky but tests show it takes ~1ms during no load situations
            t += 1
            time.sleep(0.001)

        self.video_position_received = False

        if t >= 10:
            print 'Error! Could not get the video position from VLC'
            return -1
        print self.video_position
        return self.video_position

    def video_position_callback(self, position):    # JS calls this, cant be static
        self.video_position = position
        self.video_position_received = True

    def get_video_length(self):  # TODO can this be less hacky?
        self.frame.ExecuteJavascript('javascript:python.video_length_callback(vlc.input.length)')

        t = 0
        while not self.video_length_received and t < 10:          # hacky but tests show it takes ~1ms during no load situations
            t += 1
            time.sleep(0.001)

        self.video_length_received = False

        if t >= 10:
            print 'Error! Could not get the video length from VLC'
            return -1

        return self.video_length

    def video_length_callback(self, length):
        self.video_length = length
        self.video_length_received = True

    def get_video_current_time(self):
        self.frame.ExecuteJavascript('javascript:python.video_current_time_callback(vlc.input.time)')

        t = 0
        while not self.video_current_time_received and t < 10:  # hacky but tests show it takes ~1ms during no load situations
            t += 1
            time.sleep(0.001)

        self.video_current_time_received = False

        if t >= 10:
            print 'Error! Could not get the current video time from VLC'
            return None

        return self.video_current_time

    def video_current_time_callback(self, ms):  # JS calls this, cant be static
        self.video_current_time = ms
        self.video_current_time_received = True

    def set_video_time(self, ms):
        self.frame.ExecuteJavascript('vlc.input.time = ' + str(ms) + ';')

    def change_position_callback(self, position):
        from cloudburst.media_manager import MediaManager
        MediaManager.instance().set_video_position(position)