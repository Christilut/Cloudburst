import os
import sys
import time
import codecs
import traceback

from cloudburst.util.applicationPath import getApplicationPath


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


def exceptionHook(exceptionType, exceptionValue, traceObject):
    errorMessage = os.linesep.join(traceback.format_exception(exceptionType, exceptionValue, traceObject))
    errorFile = getApplicationPath("error.log")

    try:
        applicationEncoding = cefpython.g_applicationSettings["string_encoding"]
    except:
        applicationEncoding = "utf-8"

    if type(errorMessage) == bytes:
        errorMessage = errorMessage.decode(encoding=applicationEncoding, errors="replace")
    try:
        with codecs.open(errorFile, mode='a', encoding=applicationEncoding) as fp:
            fp.write((os.linesep + '[%s] %s' + os.linesep) % (time.strftime("%d-%m-%Y %H:%M:%S"), errorMessage))
    except:
        print("cloudburst: WARNING: failed writing to error file: %s" % errorFile)

    # Convert error message to ascii before printing to prevent errors like this:
    # UnicodeEncodeError: 'charmap' codec can't encode characters
    errorMessage = errorMessage.encode('ascii', errors='replace')
    errorMessage = errorMessage.decode('ascii', errors='replace')
    print os.linesep + errorMessage + os.linesep

    cefpython.QuitMessageLoop()
    cefpython.Shutdown()
    os._exit(1)