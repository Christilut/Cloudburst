import os
import requests
from cloudburst.trakt.traktException import TraktException


class Api(object):
    def _get(self, api, *args):
        auth = None
        if os.getenv('TRAKT_USRENAME') and os.getenv('TRAKT_PASSWORD'):
            auth = (os.getenv('TRAKT_USERNAME'), os.getenv('TRAKT_PASSWORD'))

        response = requests.get(self._buildUri(api, *args), auth=auth).json()
        if isinstance(response, dict) and response.get('status', False) == 'failure':
            raise TraktException(response.get('error', 'Unknown Error'))
        return response

    def _buildUri(self, api, *args):
        url = '{0}/{1}.{2}/{3}/{4}'.format(
            'http://api.trakt.tv',
            api.strip(os.sep),
            'json',
            os.getenv('TRAKT_APIKEY'),
            os.sep.join(map(str, filter(None, args)))
        ).rstrip('/')
        print 'URL: ' + url
        return url