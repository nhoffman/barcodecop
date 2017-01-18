from os import path
from fastalite import fastalite, fastqlite, Opener

try:
    with open(path.join(path.dirname(__file__), 'data', 'ver')) as f:
        __version__ = f.read().strip().replace('-', '+', 1).replace('-', '.')
except Exception, e:
    __version__ = ''
