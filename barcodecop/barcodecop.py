#!/usr/bin/env python

"""Filter fastq files, limiting to exact barcode matches.

Input and output files may be compressed as indicated by a .bz2 or .gz
suffix.

"""

import argparse
import sys
from collections import Counter
from itertools import islice, tee, izip
import operator
import logging
from collections import namedtuple

from fastalite import fastqlite, Opener

try:
    from . import __version__
except:
    __version__ = ''


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
        return ''.join('.' if c1 == c2 and c1.isalpha() else c2
                       for c1, c2 in zip(s1, s2))


def as_fastq(seq):
    return '@{seq.description}\n{seq.seq}\n+\n{seq.qual}\n'.format(seq=seq)


def combine_dual_indices(file1, file2):
    Seq = namedtuple('Seq', ['id', 'seq'])
    for i1, i2 in izip(fastqlite(file1), fastqlite(file2)):
        assert i1.id == i2.id
        yield Seq(id=i1.id, seq=i1.seq + '+' + i2.seq)


def main(arguments=None):
    parser = argparse.ArgumentParser(
        prog='barcodecop', description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        'index', nargs='+', type=Opener(), metavar='file.fastq[.bz2|.gz]',
        help='one or two files containing index reads in fastq format')
    parser.add_argument(
        '-f', '--fastq', type=Opener(), metavar='file.fastq[.bz2|.gz]',
        help='reads to filter in fastq format')
    parser.add_argument(
        '-o', '--outfile', default=sys.stdout, type=Opener('w'),
        help='output fastq')
    parser.add_argument(
        '--snifflimit', type=int, default=10000, metavar='N',
        help='read no more than N records from the index file [%(default)s]')
    parser.add_argument(
        '--head', type=int, metavar='N',
        help='limit the output file to N records')
    parser.add_argument(
        '--min-pct-assignment', type=float, default=90.0, metavar='PERCENT',
        help=("""warn (or fail with an error; see --strict) if the
               most common barcode represents less than PERCENT of the
               total [%(default)s]"""))
    parser.add_argument(
        '--strict', action='store_true', default=False,
        help=("""fail if conditions of --min-pct-assignment are not met"""))
    parser.add_argument(
        '--invert', action='store_true', default=False,
        help='include only sequences *not* matching the most common barcode')
    # parser.add_argument('--format', choices=['fasta', 'fastq'], default='fastq')
    parser.add_argument(
        '-c', '--show-counts', action='store_true', default=False,
        help='tabulate barcode counts and exit')
    parser.add_argument(
        '-q', '--quiet', action='store_true', default=False,
        help='minimize messages to stderr')
    parser.add_argument(
        '-V', '--version', action=VersionAction, version=__version__,
        help='Print the version number and exit')

    args = parser.parse_args(arguments)

    logging.basicConfig(
        format='%(message)s',
        level=logging.ERROR if args.quiet else logging.INFO)
    log = logging.getLogger(__name__)

    if len(args.index) == 1:
        bcseqs = fastqlite(args.index[0])
    elif len(args.index) == 2:
        bcseqs = combine_dual_indices(*args.index)
    else:
        log.error('error: please specify either one or two index files')

    bc1, bc2 = tee(bcseqs, 2)

    # determine the most common barcode
    barcode_counts = Counter([str(seq.seq) for seq in islice(bc1, args.snifflimit)])
    barcodes, counts = zip(*barcode_counts.most_common())

    most_common_bc = barcodes[0]
    most_common_pct = 100 * float(counts[0])/sum(counts)
    log.info('most common barcode: {} ({}/{} = {:.2f}%)'.format(
        most_common_bc, counts[0], sum(counts), most_common_pct))

    if args.show_counts:
        for bc, count in barcode_counts.most_common():
            print('{}\t{}\t{}'.format(bc, seqdiff(most_common_bc, bc), count))
        return None

    if most_common_pct < args.min_pct_assignment:
        msg = 'frequency of most common barcode is less than {}%'.format(
            args.min_pct_assignment)
        if args.strict:
            log.error('Error: ' + msg)
            sys.exit(1)
        else:
            log.warning('Warning: ' + msg)

    if not args.fastq:
        log.error('specify a fastq format file to filter using -f/--fastq')
        sys.exit(1)

    seqs = fastqlite(args.fastq)
    filtered = islice(filter(bc2, seqs, most_common_bc, args.invert), args.head)

    for seq in filtered:
        args.outfile.write(as_fastq(seq))


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
