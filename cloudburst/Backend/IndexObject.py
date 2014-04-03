import sys

from PyQt4 import QtCore


class IndexObject(QtCore.QObject):
    def __init__(self, webView):
        super(IndexObject, self).__init__()

        self.webView = webView
        self.webView.page().mainFrame().addToJavaScriptWindowObject("pyObj", self)

    """Simple class with one slot and one read-only property."""

    def _pyVersion(self):
        """Return the Python version."""
        return sys.version

    """Python interpreter version property."""
    pyVersion = QtCore.pyqtProperty(str, fget=_pyVersion)