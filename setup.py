import os
import subprocess
from setuptools import setup, find_packages

subprocess.call(
    ('mkdir -p barcodecop/data && '
     'git describe --tags --dirty > barcodecop/data/ver.tmp'
     '&& mv barcodecop/data/ver.tmp barcodecop/data/ver '
     '|| rm -f barcodecop/data/ver.tmp'),
    shell=True, stderr=open(os.devnull, "w"))

from barcodecop import __version__

setup(
    author='Noah Hoffman',
    author_email='noah.hoffman@gmail.com',
    description=('Enforce barcode match stringency and read '
                 'quality in demultiplexed MiSeq reads'),
    url='https://github.com/nhoffman/barcodecop',
    name='barcodecop',
    packages=find_packages(),
    package_dir={'barcodecop': 'barcodecop'},
    package_data={'barcodecop': ['data/ver']},
    entry_points={'console_scripts': ['barcodecop = barcodecop.barcodecop:main']},
    version=__version__,
    test_suite='tests',
    install_requires=[
          'fastalite==0.3',
      ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
)
