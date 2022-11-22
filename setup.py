import os
import subprocess
from setuptools import setup, find_packages
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.rst").read_text()

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
    long_description_content_type='text/x-rst',
    url='https://github.com/nhoffman/barcodecop',
    name='barcodecop',
    packages=find_packages(),
    package_dir={'barcodecop': 'barcodecop'},
    package_data={'barcodecop': ['data/ver']},
    entry_points={'console_scripts': ['barcodecop = barcodecop.barcodecop:main']},
    version=__version__,
    test_suite='tests',
    install_requires=[
          'fastalite==0.4.1',
      ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
)
