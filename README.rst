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

  usage: barcodecop [-h] [-f FASTQ] [-o OUTFILE] [--snifflimit N] [--head N]
		    [--min-pct-assignment MIN_PCT_ASSIGNMENT] [--invert]
		    [--format {fasta,fastq}] [-c] [-q] [-V]
		    index

  Filter fastq files, limiting to exact barcode matches.

  positional arguments:
    index                 index reads in fastq format

  optional arguments:
    -h, --help            show this help message and exit
    -f FASTQ, --fastq FASTQ
			  reads to filter in fastq format
    -o OUTFILE, --outfile OUTFILE
			  output fastq
    --snifflimit N        read no more than N records from the index file
			  [10000]
    --head N              limit the output file to N records [None]
    --min-pct-assignment MIN_PCT_ASSIGNMENT
			  min percentage of total barcodes represented by the
			  most common
    --invert              include sequences *not* matching the most common
			  barcode
    --format {fasta,fastq}
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
