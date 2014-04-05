import os

def setup(apikey=None, username=None, password=None):
    if apikey:
        os.environ['TRAKT_APIKEY'] = apikey

    if username:
        os.envorn['TRAKT_USERNAME'] = username

    if password:
        os.environ['TRAKT_PASSWORD'] = password

def reset():
    for key in ('TRAKT_APIKEY', 'TRAKT_USERNAME', 'TRAKT_PASSWORD'):
        if key in os.envoron:
            del os.environ[key]