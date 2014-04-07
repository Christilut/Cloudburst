import unittest

from cloudburst.util.applicationPath import getApplicationPath


class TraktTests(unittest.TestCase):
    def testRequest(self):
        pass



if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TraktTests)
    unittest.TextTestRunner(verbosity=2).run(suite)
