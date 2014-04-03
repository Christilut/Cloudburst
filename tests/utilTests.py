import unittest

from cloudburst.util.applicationPath import getApplicationPath


class UtilTests(unittest.TestCase):
    def testApplicationPath(self):
        self.assertEqual('D:\\Dropbox\\Workspaces\\Python\\Cloudburst\\debug.log', getApplicationPath("debug.log"))


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(UtilTests)
    unittest.TextTestRunner(verbosity=2).run(suite)
