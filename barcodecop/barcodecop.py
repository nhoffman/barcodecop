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

try:
    from . import __version__
except:
    __version__ = ''

logging.basicConfig(format='%(message)s')
log = logging.getLogger(__name__)


class VersionAction(argparse._VersionAction):
    """Write the version string to stdout and exit"""
    def __call__(self, parser, namespace, values, option_string=None):
        formatter = parser._get_formatter()
        formatter.add_text(parser.version if self.version is None else self.version)
        sys.stdout.write(formatter.format_help())
        sys.exit(0)


def filter(barcodes, seqs, bc_match, invert=False):
    compare = operator.ne if invert else operator.eq
    for bc, seq in izip(barcodes, seqs):
        assert bc.id == seq.id
        if compare(str(bc.seq), bc_match):
            yield seq


def seqdiff(s1, s2):
    if s1 == s2:
        return s1
    else:
        return ''.join('.' if c1 == c2 else c2 for c1, c2 in zip(s1, s2))


def as_fastq(seq):
    return '@{seq.description}\n{seq.seq}\n+\n{seq.qual}\n'.format(seq=seq)


def main(arguments=None):
    parser = argparse.ArgumentParser(
        prog='barcodecop', description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('index', type=Opener(), help='index reads in fastq format')
    parser.add_argument('-f', '--fastq', type=Opener(),
                        help='reads to filter in fastq format')
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
    parser.add_argument(
        '-c', '--show-counts', action='store_true', default=False,
        help='tabulate barcode counts and exit')
    parser.add_argument(
        '-V', '--version', action=VersionAction, version=__version__,
        help='Print the version number and exit')

    args = parser.parse_args(arguments)

    bc1, bc2 = tee(fastqlite(args.index), 2)

    # determine the most common barcode
    barcode_counts = Counter([str(seq.seq) for seq in islice(bc1, args.snifflimit)])
    barcodes, counts = zip(*barcode_counts.most_common())

    most_common_bc = barcodes[0]
    most_common_pct = 100 * float(counts[0])/sum(counts)

    if args.show_counts:
        for bc, count in barcode_counts.most_common():
            print('{}\t{}\t{}'.format(bc, seqdiff(most_common_bc, bc), count))
        sys.exit()

    log.warning('most common barcode: {} ({}/{} = {:.2f}%)'.format(
        most_common_bc, counts[0], sum(counts), most_common_pct))
    assert most_common_pct > args.min_pct_assignment

    if not args.fastq:
        log.error('specify a fastq format file to filter using -f/--fastq')
        sys.exit()

    seqs = fastqlite(args.fastq)
    filtered = islice(filter(bc2, seqs, most_common_bc, args.invert), args.head)

    for seq in filtered:
        args.outfile.write(as_fastq(seq))


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
