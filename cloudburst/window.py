# Copyright (c) 2012-2013 The CEF Python authors. All rights reserved.
# License: New BSD License.
# Website: http://code.google.com/p/cefpython/

import sys
import time
import math
import win32gui
import win32api

import win32con

if sys.version_info.major == 2:
    from urllib import pathname2url as urllib_pathname2url
else:
    from urllib.request import pathname2url as urllib_pathname2url

from cloudburst.util.applicationPath import getApplicationPath

g_debug = False
g_windows = {}  # windowID(int): className
g_registeredClasses = {}


def debug(message):
    if not g_debug:
        return

    message = str("Cloudburst > Window: " + message)
    print(message)

    with open(getApplicationPath("debug.log"), "a") as debugFile:
        debugFile.write(message + "\n")


def createWindow(title, className, width, height, xPosition=None, yPosition=None, icon=None, windowHandle=None):
    if not windowHandle:
        windowHandle = {win32con.WM_CLOSE: WM_CLOSE}

    windowClass = win32gui.WNDCLASS()
    windowClass.hInstance = win32api.GetModuleHandle(None)
    windowClass.lpszClassName = className
    windowClass.style = win32con.CS_VREDRAW | win32con.CS_HREDRAW
    windowClass.hbrBackground = win32con.COLOR_WINDOW
    windowClass.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
    windowClass.lpfnWndProc = windowHandle

    global g_registeredClasses
    if not className in g_registeredClasses:
        g_registeredClasses[className] = True
        win32gui.RegisterClass(windowClass)
        debug('win32gui..RegisterClass(%s)' % className)

    if xPosition is None or yPosition is None:
        debug('Centering window on screen.')
        screenX = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
        screenY = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
        xPosition = int(math.floor((screenX - width) / 2))
        yPosition = int(math.floor((screenY - height) / 2))

        if xPosition < 0:
            xPosition = 0
        if yPosition < 0:
            yPosition = 0

    windowId = win32gui.CreateWindow(className, title,
                                     win32con.WS_OVERLAPPEDWINDOW | win32con.WS_CLIPCHILDREN | win32con.WS_VISIBLE,
                                     xPosition, yPosition, width, height, 0, 0, windowClass.hInstance, None)
    g_windows[windowId] = className
    debug("windowId = %s" % windowId)

    if icon:
        icon = getApplicationPath(icon)

        bigIcon = win32gui.LoadImage(0, icon, win32con.IMAGE_ICON, win32api.GetSystemMetrics(win32con.SM_CXICON),
                                     win32api.GetSystemMetrics(win32con.SM_CYICON), win32con.LR_LOADFROMFILE)
        smallIcon = win32gui.LoadImage(0, icon, win32con.IMAGE_ICON, win32api.GetSystemMetrics(win32con.SM_CXSMICON),
                                       win32api.GetSystemMetrics(win32con.SM_CYSMICON), win32con.LR_LOADFROMFILE)

        win32api.SendMessage(windowId, win32con.WM_SETICON, win32con.ICON_BIG, bigIcon)
        win32api.SendMessage(windowId, win32con.WM_SETICON, win32con.ICON_SMALL, smallIcon)

    return windowId


# Memory error when calling win32gui.DestroyWindow()
# after we called cefpython.CloseBrowser()
def destroyWindow(windowId):
    win32gui.DestroyWindow(windowId)
    #className = GetWindowClassName(windowID)
    #win32gui.UnregisterClass(className, None)
    #del g_windows[windowID] # Let window with this className be created again.


def getWindowClassName(windowId):
    for key in g_windows:
        if key == windowId:
            return g_windows[key]


def moveWindow(windowId, xPosition=None, yPosition=None, width=None, height=None, center=None):
    (left, top, right, bottom) = win32gui.GetWindowRect(windowId)
    if xPosition is None and yPosition is None:
        xPosition = left
        ypos = top

    if width is None and height is None:
        width = right - left
        height = bottom - top

    # Case: only ypos provided
    if xPosition is None and yPosition is not None:
        xPosition = left

    if yPosition is None and xPosition is not None:
        yPosition = top

    # Case: only height provided
    if not width:
        width = right - left

    if not height:
        height = bottom - top

    if center:
        screenx = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
        screeny = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
        xPosition = int(math.floor((screenx - width) / 2))
        yPosition = int(math.floor((screeny - height) / 2))

        if xPosition < 0:
            xPosition = 0
        if yPosition < 0:
            yPosition = 0

    win32gui.MoveWindow(windowId, xPosition, yPosition, width, height, 1)


def WM_CLOSE(windowId, message, wparam, lparam):
    destroyWindow(windowId)
    win32gui.PostQuitMessage(0)


def getLastError():
    code = win32api.GetLastError()
    return "(%d) %s" % (code, win32api.FormatMessage(code))


def messageLoop(className):
    while not win32gui.PumpWaitingMessages():
        time.sleep(0.001)


if __name__ == "__main__":
    g_debug = True
    hwnd = createWindow("Test window", "testwindow", 800, 600)
    messageLoop("testwindow")