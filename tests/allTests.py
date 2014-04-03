if __name__ == "__main__":
    import glob
    import unittest

    testFiles = [x for x in glob.glob('*Tests.py') if not x in __file__]
    moduleStrings = [fileString[0:len(fileString) - 3] for fileString in testFiles]
    suites = [unittest.defaultTestLoader.loadTestsFromName(fileString) for fileString in moduleStrings]
    testSuite = unittest.TestSuite(suites)

    print '--------------------'
    print 'STARTING > ALL TESTS'
    print '--------------------'
    print 'This will include'

    for includedFiles in testFiles:
        print '> ' + includedFiles

    textTestRunner = unittest.TextTestRunner().run(testSuite)