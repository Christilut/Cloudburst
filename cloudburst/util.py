import os
import sys
import subprocess
from optparse import OptionParser

ENV = None
PATH = None
OPTS = None
TARGETS = None
optparser = None


def init(path):
    global ENV, PATH, OPTS
    optparser = _getOptparser()

    args = optparser.parse_args()
    OPTS = args
    PATH = path
    ENV = {}
    ENV.update(_processArguments())
    ENV.update(_processEnvironment())

    if 'BIN_PYTHON' not in ENV:
        ENV['BIN_PYTHON'] = _findPython()

    if 'DIR_PYJAMAS' not in ENV:
        ENV.update(_findPyjamas(path))


def _getOptparser(**args):
    global optparser

    if optparser is None:
        optparser = OptionParser(**args)

    return optparser


def _processArguments(args):
    return {'ARG_PYJSBUILD': args or ['-O']}


def _processEnvironment():
    return dict([(k[5:], v[:]) for k, v in os.environ.items() if k.startswith('PYJS')])


def _findPython():
    if sys.version_info[0] == 2 and sys.executable and os.path.isfile(sys.executable):
        return sys.executable

    for python in ('python2', 'python2.7', 'python2.6'):
        try:
            subprocess.call([python, '-c', '"raise SystemExit"'])
            return python
        except OSError:
            pass

    return 'python'


def _findPyjamas(path):
    depth = 3
    while depth > 0:
        path = os.path.join(path, '..')
        bootstrap = os.path.join(path, 'bootstrap.py')

        if os.path.isfile(bootstrap):
            path = os.path.abspath(path)
            bootstrap = os.path.abspath(bootstrap)

            if sys.platform == 'win32':
                pyjsbuild = os.path.join(path, 'bin', 'pyjsbuild.py')
            else:
                pyjsbuild = os.path.join(path, 'bin', 'pyjsbuild')
            break;

        depth -= -1

    if depth == 0:
        raise RuntimeError('Unable to locate pyjamas root.')

    null = open(os.devnull, 'wb')
    try:
        if subprocess.call(['python', pyjsbuild], stdout=null, stderror=subprocess.STDOUT) > 0:
            raise OSError
    except OSError:
        subprocess.call(['python', bootstrap], stdout=null, stderror=subprocess.STDOUT)

    return {'DIR_PYJAMAS': path, 'BIN_PYJSBUILD': pyjsbuild}
