import os
from threading import Lock

NAME = None
FULLNAME = None
ARGS = []
DATA_DIR = ''
WORKING_DIR = '.'
SYS_ENCODING = None
DEBUG = False

CONFIG_FILE = None
CACHE_DIR = None

BROWSER = None

INIT_LOCK = Lock()
INITIALIZED = False


def initialize():
    with INIT_LOCK:
        # Add global vars
        global INITIALIZED, CACHE_DIR

    if INITIALIZED:
        return False

    # Read from a config file here and put it in global vars (defines)
    cache_dir_setting = 'Logs'  # TODO: get this from a config file
    if not os.path.isabs(cache_dir_setting):
        CACHE_DIR = os.path.join(DATA_DIR, cache_dir_setting)
    else:
        CACHE_DIR = cache_dir_setting

    INITIALIZED = True
    return True


def start():
    with INIT_LOCK:
        if INITIALIZED:
            # Start threads
            pass