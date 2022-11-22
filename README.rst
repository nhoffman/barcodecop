============
 barcodecop
============

Enforce barcode match stringency and read quality in demultiplexed MiSeq reads.

.. image:: https://github.com/nhoffman/barcodecop/actions/workflows/test.yml/badge.svg
    :target: https://github.com/nhoffman/barcodecop/actions/workflows/test.yml

Barcode mis-assignment represents a significant problem for ultra
sensitive assays that strongly interpret the presence of very low
prevalence reads within a specimen. In addition, mis-assignment of
reads between specimens can create the appearance of template
contamination in negative controls.

It turns out that barcode read quality is a predictor of barcode
mis-assignment. Wright and Vetsigian (2016)
(https://dx.doi.org/10.1186%2Fs12864-016-3217-x) showed that an
average barcode quality score threshold of 26 prevented most read
mis-assignment on the Illumina platform.

In addition, the onboard software used for demultiplexing on the
Illumina MiSeq cannot be configured to enforce exact barcode
matches. As a result, a minority of reads (up to about 5% in my tests)
are assigned to a specimen on the basis of a partial barcode
match. Somewhat anecdotally, these less-than-exact matches appear to
have a higher likelihood of mis-assignment as well, but the effect is
dependent on barcode sequence and which combinations of barcodes are
used in the same library.

This package provides the ``barcodecop`` command that uses the index
reads to determine the most prevalent barcode sequence, and removes
reads without exact barcode matches from an accompanying fastq
file. It also filters reads based on average barcode quality score.

Command line arguments::

  usage: barcodecop [-h] [-o OUTFILE] [--snifflimit N] [--head N] [--invert] [-q] [-V] (-c | -f file.fastq[.bz2|.gz]) [--match-filter]
                    [--min-pct-assignment PERCENT] [--strict] [-b FILE] [-C FILE] [--allow-empty] [--qual-filter] [-p MIN_QUAL] [--encoding {phred}]
                    file.fastq[.bz2|.gz] [file.fastq[.bz2|.gz] ...]

  Filter fastq files by enforcing exact barcode match and quality score.

  Input and output files may be compressed as indicated by a .bz2 or .gz
  suffix.

  positional arguments:
    file.fastq[.bz2|.gz]  one or two files containing index reads in fastq format

  options:
    -h, --help            show this help message and exit
    -o OUTFILE, --outfile OUTFILE
                          output fastq
    --snifflimit N        read no more than N records from the index file [10000]
    --head N              limit the output file to N records
    --invert              include only sequences failing filtering criteria
    -q, --quiet           minimize messages to stderr
    -V, --version         Print the version number and exit
    -c, --show-counts     tabulate barcode counts and exit
    -f file.fastq[.bz2|.gz], --fastq file.fastq[.bz2|.gz]
                          reads to filter in fastq format

  Barcode matching options:
    --match-filter        filter reads based on exact match to most common barcode [default: no match filter]
    --min-pct-assignment PERCENT
                          warn (or fail with an error; see --strict) if the most common barcode represents less than PERCENT of the total [90.0]
    --strict              fail if conditions of --min-pct-assignment are not met
    -b FILE, --barcode-counts FILE
                          tabulate barcode counts and store as a CSV
    -C FILE, --read-counts FILE
                          tabulate read counts and store as a CSV
    --allow-empty         accept fastq files which contain zero length seqs/qual strings[default: do not allow empty seqs in fastq files]

  Barcode quality filtering options:
    --qual-filter         filter reads based on minimum index quality [default: no quality filter]
    -p MIN_QUAL, --min-qual MIN_QUAL
                          reject seqs with mean barcode quality score less than this value; for dual index, both barcodes must meet the threshold [26]
    --encoding {phred}    quality score encoding; see https://en.wikipedia.org/wiki/FASTQ_format [phred]


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
