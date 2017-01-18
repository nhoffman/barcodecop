import os
import subprocess
from setuptools import setup, find_packages

subprocess.call(
    ('mkdir -p fastalite/data && '
     'git describe --tags --dirty > fastalite/data/ver.tmp'
     '&& mv fastalite/data/ver.tmp fastalite/data/ver '
     '|| rm -f fastalite/data/ver.tmp'),
    shell=True, stderr=open(os.devnull, "w"))

from fastalite import __version__

setup(
    author='Noah Hoffman',
    author_email='noah.hoffman@gmail.com',
    description='Enforce exact barcode matches in demultiplexed MiSeq reads',
    url='https://github.com/nhoffman/fastalite',
    name='fastalite',
    packages=find_packages(),
    package_dir={'fastalite': 'fastalite'},
    package_data={'fastalite': ['data/ver']},
    version=__version__,
    test_suite='tests',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 2.7',
    ],
)
