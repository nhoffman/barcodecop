============
 barcodecop
============

Enforce exact barcode matches in demultiplexed MiSeq reads

The problem is rather silly, really: the onboard software used for
demultiplexing on the Illumina MiSeq cannot be configured to enforce
exact barcode matches. As a result, a minority of reads (up to about
5% in my tests) are assigned to a specimen on the basis of a partial
barcode match. It turns out that some fraction of these
less-than-exact matches are mis-assigned (as of course are the exact
matches, but we can't identify these as easily). This mis-assignment
is a problem for ultra sensitive assays. This package provides a tiny
script that uses the index reads to determine the most prevalent
barcode sequence and filter reads from an accompanying fastq file.


Installation
============

Install from PyPi using pip::

  pip install barcodecop

Or install directly from the git repository::

  pip install git+https://github.com/nhoffman/barcodecop.git


Testing
=======

Run all tests like this::

  python setup.py test
