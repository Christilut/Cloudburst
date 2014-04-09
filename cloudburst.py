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
from cloudburst.MediaManager import MediaManager
from cloudburst.exceptions.exceptionHook import exceptionHook
from cloudburst.util.applicationPath import getApplicationPath
from cloudburst.vlcInterface import VlcInterface

class Cloudburst():
    CEF_DEBUG = False # If true, spams console with CEFPython debug messages
    isLoaded = False # True is HTML page is done loading
    isRunning = False # Thread running
    vlcInterface = None

    def __init__(self):

        self.isRunning = True

        sys.excepthook = exceptionHook
        applicationSettings = dict()

        if self.CEF_DEBUG:
            window.g_debug = True
            applicationSettings['debug'] = True
            applicationSettings['release_dcheck_enabled'] = True

        applicationSettings['log_file'] = getApplicationPath('debug.log')
        applicationSettings['log_severity'] = cefpython.LOGSEVERITY_INFO
        applicationSettings['browser_subprocess_path'] = '%s/%s' % (cefpython.GetModuleDirectory(), 'subprocess')
        cefpython.Initialize(applicationSettings)

        browserSettings = dict()
        browserSettings['file_access_from_file_urls_allowed'] = True
        browserSettings['universal_access_from_file_urls_allowed'] = True

        windowHandles = {
            win32con.WM_CLOSE: self.closeWindow,
            win32con.WM_DESTROY: self.quitApplication,
            win32con.WM_SIZE: cefpython.WindowUtils.OnSize,
            win32con.WM_SETFOCUS: cefpython.WindowUtils.OnSetFocus,
            win32con.WM_ERASEBKGND: cefpython.WindowUtils.OnEraseBackground
        }

        windowHandle = window.createWindow(title='Cloudburst', className='Cloudburst', width=800, height=700,
                                           icon=getApplicationPath('res/images/cloudburst.ico'), windowHandle=windowHandles)

        windowInfo = cefpython.WindowInfo()
        windowInfo.SetAsChild(windowHandle)
        browser = cefpython.CreateBrowserSync(windowInfo, browserSettings, navigateUrl=getApplicationPath("res/views/vlc-test.html"))

        jsBindings = cefpython.JavascriptBindings(bindToFrames=False, bindToPopups=True)
        # jsBindings.SetProperty("pyProperty", "This was set in Python") # TODO figure out how to set these properties in js
        # self.jsBindings.SetProperty("pyConfig", ["This was set in Python",
        #         {"name": "Nested dictionary", "isNested": True},
        #         [1,"2", None]])

        self.vlcInterface = VlcInterface.Instance()
        self.vlcInterface.setBrowser(browser)

        jsBindings.SetObject("python", self.vlcInterface)
        browser.SetJavascriptBindings(jsBindings)

        browser.SetClientCallback("OnLoadEnd", self.OnLoadEnd)

        mediaManager = MediaManager.Instance()

        # blocking loop
        cefpython.MessageLoop()
        cefpython.Shutdown()


        # Shuts down threads and cancels running timers (these would otherwise block)
        mediaManager.shutdown()
        print 'Shutdown complete'

    def closeWindow(self, windowHandle, message, wparam, lparam):
        browser = cefpython.GetBrowserByWindowHandle(windowHandle)
        browser.CloseBrowser()
        return win32gui.DefWindowProc(windowHandle, message, wparam, lparam)


    def quitApplication(self, windowHandle, message, wparam, lparam):
        self.isRunning = False
        win32gui.PostQuitMessage(0)
        return 0

    def OnLoadEnd(self, browser, frame, httpCode):
        self.isLoaded = True

if __name__ == "__main__":

    # Set data dirs
    appdirs.appauthor = 'Cloudburst'        # USAGE: https://pypi.python.org/pypi/appdirs/1.2.0
    appdirs.appname = 'Cloudburst'
    appdirs.dirs = appdirs.AppDirs(appdirs.appname, appdirs.appauthor)


    Cloudburst() # blocking until window closed
