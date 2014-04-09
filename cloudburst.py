import platform

if platform.architecture()[0] != "32bit":
    raise Exception("Architecture not supported: %s" % platform.architecture()[0])

import os
import sys

libcefDll = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'libcef.dll')
if os.path.exists(libcefDll):  # If the libcef dll exists use that for imports
    if 0x02070000 <= sys.hexversion < 0x03000000:
        import cefpython_py27 as cefpython  # Import for python 2.7
    elif 0x03000000 <= sys.hexversion < 0x04000000:
        import cefpython_py32 as cefpython  # Import for python 3.2
    else:
        raise Exception('Unsupported python version: %s' % sys.version)
else:
    from cefpython3 import cefpython  # Import cefpython from package

import win32con
import win32gui
import appdirs

from cloudburst import window
from cloudburst.media_manager import MediaManager
from cloudburst.exceptions.exceptionHook import exceptionHook
from cloudburst.util.applicationPath import getApplicationPath
from cloudburst.media.vlc import VLC


class Cloudburst():
    CEF_DEBUG = False # If true, spams console with CEFPython debug messages
    html_loaded = False # True is HTML page is done loading
    running = False # Thread running
    vlc = None

    def __init__(self):

        self.running = True

        sys.excepthook = exceptionHook
        applicationsettings = dict()

        if self.CEF_DEBUG:
            window.g_debug = True
            applicationsettings['debug'] = True
            applicationsettings['release_dcheck_enabled'] = True

        applicationsettings['log_file'] = getApplicationPath('debug.log')
        applicationsettings['log_severity'] = cefpython.LOGSEVERITY_INFO
        applicationsettings['browser_subprocess_path'] = '%s/%s' % (cefpython.GetModuleDirectory(), 'subprocess')
        cefpython.Initialize(applicationsettings)

        browsersettings = dict()
        browsersettings['file_access_from_file_urls_allowed'] = True
        browsersettings['universal_access_from_file_urls_allowed'] = True

        windowhandles = {
            win32con.WM_CLOSE: self.close_window,
            win32con.WM_DESTROY: self.quit,
            win32con.WM_SIZE: cefpython.WindowUtils.OnSize,
            win32con.WM_SETFOCUS: cefpython.WindowUtils.OnSetFocus,
            win32con.WM_ERASEBKGND: cefpython.WindowUtils.OnEraseBackground
        }

        windowhandle = window.createWindow(title='Cloudburst', className='Cloudburst', width=800, height=700,
                                           icon=getApplicationPath('res/images/cloudburst.ico'), windowHandle=windowhandles)

        windowinfo = cefpython.WindowInfo()
        windowinfo.SetAsChild(windowhandle)
        browser = cefpython.CreateBrowserSync(windowinfo, browsersettings, navigateUrl=getApplicationPath("res/views/vlc-test.html"))

        jsbindings = cefpython.JavascriptBindings(bindToFrames=False, bindToPopups=True)
        # jsBindings.SetProperty("pyProperty", "This was set in Python") # TODO figure out how to set these properties in js
        # self.jsBindings.SetProperty("pyConfig", ["This was set in Python",
        #         {"name": "Nested dictionary", "isNested": True},
        #         [1,"2", None]])

        self.vlc = VLC.instance()
        self.vlc.set_browser(browser)

        jsbindings.SetObject("python", self.vlc)
        browser.SetJavascriptBindings(jsbindings)

        browser.SetClientCallback("OnLoadEnd", self.on_load_end)

        media_manager = MediaManager.instance()

        # blocking loop
        cefpython.MessageLoop()
        cefpython.Shutdown()


        # Shuts down threads and cancels running timers (these would otherwise block)
        media_manager.shutdown()
        print 'Shutdown complete'

    def close_window(self, windowhandle, message, wparam, lparam):
        browser = cefpython.GetBrowserByWindowHandle(windowhandle)
        browser.CloseBrowser()
        return win32gui.DefWindowProc(windowhandle, message, wparam, lparam)

    def quit(self, windowhandle, message, wparam, lparam):
        self.running = False
        win32gui.PostQuitMessage(0)
        return 0

    def on_load_end(self, browser, frame, http_code):
        self.html_loaded = True

if __name__ == "__main__":

    # Set data dirs
    appdirs.appauthor = 'Cloudburst'        # USAGE: https://pypi.python.org/pypi/appdirs/1.2.0
    appdirs.appname = 'Cloudburst'
    appdirs.dirs = appdirs.AppDirs(appdirs.appname, appdirs.appauthor)


    Cloudburst()                            # blocking until window closed
