from os import path

# default values
MIN_QUAL = 26
QUAL_OFFSET = 33  # default is set for Illumina reads

try:
    with open(path.join(path.dirname(__file__), 'data', 'ver')) as f:
        __version__ = f.read().strip().replace('-', '+', 1).replace('-', '.')
except Exception, e:
    __version__ = ''
