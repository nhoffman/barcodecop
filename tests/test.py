#!/usr/bin/env python

import os
from os import path
import inspect
from unittest import TestCase

from fastalite import fastalite, fastqlite, Opener

outdir = 'test_output'


def mkoutdir(basedir):
    stacknames = [x[3] for x in inspect.stack()]
    testfun = [name for name in stacknames if name.startswith('test_')][0]
    pth = path.join(basedir, testfun)

    try:
        os.makedirs(pth)
    except OSError:
        pass

    return pth
