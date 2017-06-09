============
 barcodecop
============

Enforce exact barcode matches in demultiplexed MiSeq reads

.. image:: https://travis-ci.org/nhoffman/barcodecop.svg?branch=master
    :target: https://travis-ci.org/nhoffman/barcodecop

The onboard software used for demultiplexing on the Illumina MiSeq
cannot be configured to enforce exact barcode matches. As a result, a
minority of reads (up to about 5% in my tests) are assigned to a
specimen on the basis of a partial barcode match. It turns out that
some fraction of these less-than-exact matches are mis-assigned from
other specimens (as of course are some smaller fraction of the exact
matches, but we can't identify these as easily). This mis-assignment
is a problem for ultra sensitive assays that attempt to draw
conclusions from the presence of very low prevalence reads.

This package provides the ``barcodecop`` command that uses the index
reads to determine the most prevalent barcode sequence and filter
reads from an accompanying fastq file.

Command line arguments::

  usage: barcodecop [-h] [-f file.fastq[.bz2|.gz]] [-o OUTFILE] [--snifflimit N]
                    [--head N] [--invert] [-q] [-V]
                    [--min-pct-assignment PERCENT] [--strict] [-c]
                    [--qual-filter] [-p MIN_QUAL] [--encoding {phred}]
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
    --invert              include only sequences failing filtering criteria
    -q, --quiet           minimize messages to stderr
    -V, --version         Print the version number and exit

  Barcode matching options:
    --min-pct-assignment PERCENT
                          warn (or fail with an error; see --strict) if the most
                          common barcode represents less than PERCENT of the
                          total [90.0]
    --strict              fail if conditions of --min-pct-assignment are not met
    -c, --show-counts     tabulate barcode counts and exit

  Barcode quality filtering options:
    --qual-filter         filter reads based on minimum index quality [default:
                          no quality filter]
    -p MIN_QUAL, --min-qual MIN_QUAL
                          reject seqs with mean barcode quality score less than
                          this value; for dual index, both barcodes must meet
                          the threshold [26]
    --encoding {phred}    quality score encoding; see
                          https://en.wikipedia.org/wiki/FASTQ_format [phred]


Both single and dual-indexing are supported. For example::

  barcodecop input_I1.fastq --fastq input_R1.fastq -o output_R1.fastq

Or, using a dual index::

  barcodecop input_I1.fastq input_I2.fastq --fastq input_R1.fastq -o output_R1.fastq


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
