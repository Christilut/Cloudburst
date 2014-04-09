import platform
from cloudburst.vlcInterface import VlcInterface

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

import cloudburst

import locale

import win32con
import win32gui
import appdirs
import threading

from cloudburst import window
from cloudburst.exceptions.exceptionHook import exceptionHook
from cloudburst.util.applicationPath import getApplicationPath
from cloudburst.StreamingPlayer.StreamingPlayer import StreamingPlayer


def main():
    cloudburst.FULLNAME = os.path.normpath(os.path.abspath(__file__))
    cloudburst.NAME = os.path.basename(cloudburst.FULLNAME)
    cloudburst.WORKING_DIR = os.path.dirname(cloudburst.FULLNAME)
    cloudburst.DATA_DIR = cloudburst.WORKING_DIR
    cloudburst.ARGS = sys.argv[1:]
    cloudburst.DEBUG = True

    cloudburst.CONFIG_FILE = os.path.join(cloudburst.DATA_DIR, 'config.ini')

    try:
        locale.setlocale(locale.LC_ALL, '')
        cloudburst.SYS_ENCODING = locale.getpreferredencoding()
    except (locale.Error, IOError):
        cloudburst.SYS_ENCODING = None

    # When there is no encoding found or wrongly configured, force utf-8
    if not cloudburst.SYS_ENCODING or cloudburst.SYS_ENCODING in ('ANSI_X3.4-1968', 'US-ASCII', 'ASCII'):
        cloudburst.SYS_ENCODING = 'UTF-8'

    # TODO: Find out why?
    if not hasattr(sys, 'setdefaultencoding'):
        reload(sys)

    threading.currentThread().name = 'Main'

    cloudburst.initialize()
    cloudburst.start()

    sys.excepthook = exceptionHook
    applicationSettings = dict()

    if cloudburst.DEBUG:
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
        win32con.WM_CLOSE: closeWindow,
        win32con.WM_DESTROY: quitApplication,
        win32con.WM_SIZE: cefpython.WindowUtils.OnSize,
        win32con.WM_SETFOCUS: cefpython.WindowUtils.OnSetFocus,
        win32con.WM_ERASEBKGND: cefpython.WindowUtils.OnEraseBackground
    }

    windowHandle = window.createWindow(title='Cloudburst', className='Cloudburst', width=800, height=700,
                                       icon=getApplicationPath('res/images/cloudburst.ico'), windowHandle=windowHandles)

    windowInfo = cefpython.WindowInfo()
    windowInfo.SetAsChild(windowHandle)
    browser = cefpython.CreateBrowserSync(windowInfo, browserSettings, navigateUrl=getApplicationPath("res/views/home.tmpl"))

    browser.SetClientCallback("OnLoadEnd", OnLoadEnd)

    cloudburst.BROWSER = browser

    # blocking loop
    cefpython.MessageLoop()
    cefpython.Shutdown()


def closeWindow(windowHandle, message, wparam, lparam):
    browser = cefpython.GetBrowserByWindowHandle(windowHandle)
    browser.CloseBrowser()
    return win32gui.DefWindowProc(windowHandle, message, wparam, lparam)


def quitApplication(windowHandle, message, wparam, lparam):
    win32gui.PostQuitMessage(0)
    return 0


def OnLoadEnd(browser, frame, httpCode):
    pass


class Home():
    def title(self):
        return "Frog 2 Page"

    def body(self):
        return " ... more info about frogs ..."

if __name__ == '__main__':
    Home()
    main()

"""class Cloudburst():
    DEBUG = True
    isLoaded = False # True is HTML page is done loading
    isRunning = False # Thread running
    vlcInterface = None

    def __init__(self):

        self.isRunning = True

        sys.excepthook = exceptionHook
        applicationSettings = dict()

        if self.DEBUG:
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

        jsBindings = cefpython.JavascriptBindings(
                bindToFrames=False, bindToPopups=True)
        jsBindings.SetProperty("pyProperty", "This was set in Python")
        jsBindings.SetProperty("pyConfig", ["This was set in Python",
                {"name": "Nested dictionary", "isNested": True},
                [1,"2", None]])

        self.vlcInterface = VlcInterface(browser)

        jsBindings.SetObject("external", self.vlcInterface)
        browser.SetJavascriptBindings(jsBindings)

        browser.SetClientCallback("OnLoadEnd", self.OnLoadEnd)


        # Start the streaming back end
        streamingPlayer = StreamingPlayer(self)
        streamingPlayer.start()
        # streamingPlayer.OpenTorrent('res/torrents/big_movie.torrent') # TEMP

        # blocking loop
        cefpython.MessageLoop()
        cefpython.Shutdown()


        # Shuts down threads and cancels running timers (these would otherwise block)
        streamingPlayer.Shutdown()

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


    Cloudburst() # blocking until window closed"""