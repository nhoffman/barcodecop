============
 barcodecop
============

Enforce exact barcode matches in demultiplexed MiSeq reads

.. image:: https://travis-ci.org/nhoffman/barcodecop.svg?branch=master
    :target: https://travis-ci.org/nhoffman/barcodecop

The problem is rather silly, really: the onboard software used for
demultiplexing on the Illumina MiSeq cannot be configured to enforce
exact barcode matches. As a result, a minority of reads (up to about
5% in my tests) are assigned to a specimen on the basis of a partial
barcode match. It turns out that some fraction of these
less-than-exact matches are mis-assigned from other specimens (as of
course are some smaller fraction of the the exact matches, but we
can't identify these as easily). This mis-assignment is a problem for
ultra sensitive assays that look for very low prevalence reads. This
package provides a tiny script that uses the index reads to determine
the most prevalent barcode sequence and filter reads from an
accompanying fastq file.

Command line arguments::

  usage: barcodecop [-h] [-f file.fastq[.bz2|.gz]] [-o OUTFILE] [--snifflimit N]
		    [--head N] [--min-pct-assignment PERCENT] [--invert] [-c]
		    [-q] [-V]
		    file.fastq[.bz2|.gz] [file.fastq[.bz2|.gz] ...]

  Filter fastq files, limiting to exact barcode matches.

  Input and output files may be compressed as indicated by a .bz2 or .gz
  suffix.

  positional arguments:
    file.fastq[.bz2|.gz]  one or two files containing index reads in fastq
			  format

  optional arguments:
    -h, --help            show this help message and exit
    -f file.fastq[.bz2|.gz], --fastq file.fastq[.bz2|.gz]
			  reads to filter in fastq format
    -o OUTFILE, --outfile OUTFILE
			  output fastq
    --snifflimit N        read no more than N records from the index file
			  [10000]
    --head N              limit the output file to N records
    --min-pct-assignment PERCENT
			  raise error unless the most common barcode represents
			  at least PERCENT of the total [90.0]
    --invert              include only sequences *not* matching the most common
			  barcode
    -c, --show-counts     tabulate barcode counts and exit
    -q, --quiet           minimize messages to stderr
    -V, --version         Print the version number and exit


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
