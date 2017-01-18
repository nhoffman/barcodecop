#!/usr/bin/env python

"""Filter fastq files, limiting to exact barcode matches.

"""

import argparse
import sys
from collections import Counter
from itertools import islice, tee, izip
import operator
import logging

from fastalite import fastqlite, Opener

logging.basicConfig(format='%(message)s')
log = logging.getLogger(__name__)


def filter(barcodes, seqs, bc_match, invert=False):
    compare = operator.ne if invert else operator.eq
    for bc, seq in izip(barcodes, seqs):
        assert bc.id == seq.id
        if compare(str(bc.seq), bc_match):
            yield seq


def as_fastq(seq):
    return '@{seq.description}\n{seq.seq}\n+{seq.qual}\n'


def main(arguments):
    parser = argparse.ArgumentParser(
        prog='barcodecop', description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('index_reads', type=Opener())
    parser.add_argument('inseqs', type=Opener())
    parser.add_argument(
        '-o', '--outfile', default=sys.stdout, type=Opener('w'),
        help='output fastq')
    parser.add_argument(
        '--snifflimit', type=int, default=10000, metavar='N',
        help='read no more than N records from the index file [%(default)s]')
    parser.add_argument(
        '--head', type=int, metavar='N',
        help='limit the output file to N records [%(default)s]')
    parser.add_argument(
        '--min-pct-assignment', type=float, default=90.0,
        help='min percentage of total barcodes represented by the most common')
    parser.add_argument(
        '--invert', action='store_true', default=False,
        help='include sequences *not* matching the most common barcode')
    parser.add_argument('--format', choices=['fasta', 'fastq'], default='fastq')

    args = parser.parse_args(arguments)

    bc1, bc2 = tee(fastqlite(args.index_reads), 2)

    # determine the most common barcode
    barcode_counts = Counter([str(seq.seq) for seq in islice(bc1, args.snifflimit)])
    barcodes, counts = zip(*barcode_counts.most_common())

    most_common_bc = barcodes[0]
    most_common_pct = 100 * float(counts[0])/sum(counts)
    log.warning('most common barcode: {} ({}/{} = {:.2f}%)'.format(
        most_common_bc, counts[0], sum(counts), most_common_pct))
    assert most_common_pct > args.min_pct_assignment

    seqs = fastqlite(args.inseqs)
    filtered = islice(filter(bc2, seqs, most_common_bc, args.invert), args.head)

    for seq in filtered:
        args.outfile.write(as_fastq(seq))


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
