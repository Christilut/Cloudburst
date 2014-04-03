import re
import os
import sys


def getApplicationPath(filename=None):
    if filename is None:
        filename = ''

    # Relative path
    if not filename.startswith("/") and not filename.startswith("\\") and (not re.search(r"^[\w-]+:", filename)):
        if hasattr(sys, 'frozen'):  # TODO: Find out what frozen attribute is.
            path = os.path.dirname(sys.executable)
        else:
            path = os.getcwd()

        path += os.sep + filename
        path = re.sub(r'[/\\]+', re.escape(os.sep), path)
        path = re.sub(r'[/\\]+$', '', path)  # TODO: Find out what this regex does.
        return path
    return str(filename)