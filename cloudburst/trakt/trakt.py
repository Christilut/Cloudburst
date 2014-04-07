try:
    from urllib import quote_plus
except ImportError:
    from urllib.parse import quote_plus

import os
import time
import requests
from hashlib import md5
import cPickle as pickle

API_KEY = 'f4ec57f2eeb651e5719cc1adf8b3944c'
TRAKT_URL =  'http://api.trakt.tv/%s.json/%s%s'


class Trakt(object):
    def __init__(self, cacheLocation, maxAge=7200):
        self.cacheLocation = cacheLocation
        self.maxAge = maxAge

    def request(self, action, values=None, params=None):
        if params is None:
            params = []
        elif isinstance(params, basestring):
            params = [params]

        params = [x for x in params if x]

        if values is None:
            values = {}

        url = TRAKT_URL % (action, API_KEY, ('/' + '/'.join(params)) if params else '')

        cacheFile = os.path.join(self.cacheLocation, md5(url).hexdigest())
        if os.path.exists(cacheFile):
            print '>>>>>>>>>>>>>>>>>> From cache'

            cacheModifiedTime = os.stat(cacheFile).st_mtime
            if cacheModifiedTime < time.time() - self.maxAge:
                print ">>>>>> Outdated cache, redownload"
                os.remove(cacheFile)
                response = self.request(action, values, params)
            else:
                response = pickle.load(open(cacheFile, 'rb'))
        else:  # Get the contents from the internet
            print 'From Internet'
            response = requests.get(url).json()
            pickle.dump(response, open(cacheFile, "wb"))

        if isinstance(response, dict) and response.get('status', False) == 'failure':
            raise Exception(response.get('error', 'Unknown Error'))

        return self.parseResponse(response)

    def parseResponse(self, response):
        if response is None:
            return {'success': False, 'message': 'Unknown failure'}

        if type(response) is not dict or 'status' not in response:

            return {'success': True, 'data': response}