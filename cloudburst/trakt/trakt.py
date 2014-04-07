import os
import time
import shutil
import requests
from hashlib import md5
import cPickle as pickle
from urlparse import urlsplit
from StringIO import StringIO

from PIL import Image

API_KEY = 'f4ec57f2eeb651e5719cc1adf8b3944c'
TRAKT_URL =  'http://api.trakt.tv/%s.json/%s%s'
IMAGE_URL = 'https://zapp.trakt.us/images/posters_movies/%s-%s.jpg'


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

        print url

        if isinstance(response, dict) and response.get('status', False) == 'failure':
            raise Exception(response.get('error', 'Unknown Error'))

        return self.parseResponse(response)

    def parseResponse(self, response):
        if response is None:
            return {'success': False, 'message': 'Unknown failure'}

        if type(response) is not dict or 'status' not in response:
            self.getPosters(response)
            return {'success': True, 'data': response}

    def getPosters(self, response):
        size = 138
        for item in response:
            if item.get('poster') is not None:
                coverPath = item.get('poster')
            elif item.get('images')['poster'] is not None:
                coverPath = item.get('images')['poster']

            filename, extension = os.path.splitext(coverPath)
            filename = filename.rsplit('/', 1)[1].split('.')[0]
            url = IMAGE_URL % (filename, size)

            coverFile = os.path.join(self.cacheLocation, md5(url).hexdigest())
            if os.path.exists(coverFile):
                pass  # Skip for now
            else:
                r = requests.get(url)
                with open(coverFile, 'wb') as c:
                    c.write(r.content)