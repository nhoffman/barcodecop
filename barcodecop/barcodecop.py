#!/usr/bin/env python

"""Filter fastq files by enforcing exact barcode match and quality score.

Input and output files may be compressed as indicated by a .bz2 or .gz
suffix.

"""

import argparse
import sys
import csv
from collections import Counter
import logging
from collections import namedtuple

from itertools import islice, tee
try:
    from itertools import filterfalse, zip_longest
except ImportError:
    from itertools import izip_longest as zip_longest
    from itertools import ifilterfalse as filterfalse
    from itertools import ifilter as filter


from fastalite import fastqlite, Opener

try:
    from . import __version__
except:
    __version__ = ''

# default values
MIN_QUAL = 26


class VersionAction(argparse._VersionAction):

    """Write the version string to stdout (rather than stderr) and exit"""

    def __call__(self, parser, namespace, values, option_string=None):
        formatter = parser._get_formatter()
        formatter.add_text(
            parser.version if self.version is None else self.version)
        sys.stdout.write(formatter.format_help())
        sys.exit(0)


def get_match_filter(barcode):
    """Return a function for filtering a pair of (seq, bc) namedtuple
    pairs; the function returns True if bc.seq == barcode

    """

    def filterfun(pair):
        seq, bc = pair
        return str(bc.seq) == barcode

    return filterfun


def get_qual_filter(min_qual, encoding, paired=False):
    """Return a function for filtering a pair of (seq, bc) namedtuple
    pairs. The function returns True if the average barcode quality
    score calculated using the provided encoding method is at least
    min_qual. If``paired`` is True, ``bc`` must be a namedtuple with
    attributes qual and qual2; the function returns True if the average
    barcode quality score calculated using the provided encoding method
    is at least min_qual.  The function defined for each encoding method
    is specified as ``get_{}_encoding``.  Currently only Sanger phred
    encoding is supported -- see ``get_phred_encoding``.

    """

    encoding = globals()['get_{}_encoding'.format(encoding)]()

    if paired:
        def filterfun(pair):
            seq, bc = pair
            return (check_score(encoding, min_qual, bc.qual) and
                    check_score(encoding, min_qual, bc.qual2))
    else:
        def filterfun(pair):
            seq, bc = pair
            return check_score(encoding, min_qual, bc.qual)

    return filterfun


def get_phred_encoding():
    """Return a dict of {ascii character: quality score} providing an
    encoding of ASCII characters 33 to 126 corresponding to values 0
    to 93.

    see https://en.wikipedia.org/wiki/FASTQ_format

    """

    offset = 33
    return {chr(i): i - offset for i in range(offset, 127)}


def check_score(encoding, min_qual, qual_str):
    """Return True if the average quality score is at least min_qual

    """
    qscores = [encoding[q] for q in qual_str]
    return sum(qscores) >= min_qual * len(qscores)


def seqdiff(s1, s2):
    if s1 == s2:
        return s1
    else:
        return ''.join('.' if c1 == c2 and c1.isalpha() else c2
                       for c1, c2 in zip(s1, s2))


def as_fastq(seq):
    return u'@{seq.description}\n{seq.seq}\n+\n{seq.qual}\n'.format(seq=seq)


def combine_dual_indices(file1, file2):
    Seq = namedtuple('Seq', ['id', 'seq', 'qual', 'qual2'])
    for i1, i2 in zip_longest(fastqlite(file1), fastqlite(file2)):
        assert i1.id == i2.id
        yield Seq(id=i1.id, seq=i1.seq + '+' + i2.seq, qual=i1.qual, qual2=i2.qual)


def close_all_files(args):
    for name, obj in args.__dict__.items():
        if (obj and hasattr(obj, 'close') and
            hasattr(obj, 'closed') and hasattr(obj, 'name')):
            if not obj.closed:
                obj.close()


def main(arguments=None):
    parser = argparse.ArgumentParser(
        prog='barcodecop', description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        'index', nargs='+', type=Opener(), metavar='file.fastq[.bz2|.gz]',
        help='one or two files containing index reads in fastq format')
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
        '--invert', action='store_true', default=False,
        help='include only sequences failing filtering criteria')
    parser.add_argument(
        '-q', '--quiet', action='store_true', default=False,
        help='minimize messages to stderr')
    parser.add_argument(
        '-V', '--version', action=VersionAction, version=__version__,
        help='Print the version number and exit')

    processing_options = parser.add_mutually_exclusive_group(required=True)
    processing_options.add_argument(
        '-c', '--show-counts', action='store_true', default=False,
        help='tabulate barcode counts and exit')
    processing_options.add_argument(
        '-f', '--fastq', type=Opener(), metavar='file.fastq[.bz2|.gz]',
        help='reads to filter in fastq format')

    match_options = parser.add_argument_group('Barcode matching options')

    match_options.add_argument(
        '--match-filter', action='store_true', default=False,
        help=('filter reads based on exact match to most common barcode '
              '[default: no match filter]'))
    match_options.add_argument(
        '--min-pct-assignment', type=float, default=90.0, metavar='PERCENT',
        help=("""warn (or fail with an error; see --strict) if the
               most common barcode represents less than PERCENT of the
               total [%(default)s]"""))
    match_options.add_argument(
        '--strict', action='store_true', default=False,
        help=("""fail if conditions of --min-pct-assignment are not met"""))
    match_options.add_argument(
        '-b', '--barcode-counts', type=argparse.FileType('w'), metavar='FILE',
        help='tabulate barcode counts and store as a CSV')
    match_options.add_argument(
        '-C', '--read-counts', type=argparse.FileType('w'), metavar='FILE',
        help='tabulate read counts and store as a CSV')
    match_options.add_argument(
        '--allow-empty', action='store_true', default=False,
        help=('accept fastq files which contain zero length seqs/qual strings'
              '[default: do not allow empty seqs in fastq files]'))

    qual_options = parser.add_argument_group('Barcode quality filtering options')

    qual_options.add_argument(
        '--qual-filter', action='store_true', default=False,
        help=('filter reads based on minimum index quality '
              '[default: no quality filter]'))
    qual_options.add_argument(
        '-p', '--min-qual', type=int, default=MIN_QUAL,
        help="""reject seqs with mean barcode quality score less than
        this value; for dual index, both barcodes must meet the
        threshold [%(default)s]""")
    qual_options.add_argument(
        '--encoding', default='phred', choices=['phred'],
        help="""quality score encoding; see
             https://en.wikipedia.org/wiki/FASTQ_format [%(default)s]""")

    args = parser.parse_args(arguments)

    logging.basicConfig(
        format='%(message)s',
        level=logging.ERROR if args.quiet else logging.WARNING)
    log = logging.getLogger(__name__)

    # when provided with dual barcodes, concatenate into a single
    # namedtuple with attributes qual and qual1; generate a filter
    # function appropriate for either case.
    if len(args.index) == 1:
        bcseqs = fastqlite(args.index[0])
        qual_filter = get_qual_filter(args.min_qual, args.encoding)
    elif len(args.index) == 2:
        qual_filter = get_qual_filter(args.min_qual, args.encoding, paired=True)
        bcseqs = combine_dual_indices(*args.index)
    else:
        log.error('error: please specify either one or two index files')

    # use bc1 to determine most common barcode
    bc1, bc2 = tee(bcseqs, 2)

    iseqs = [str(seq.seq) for seq in islice(bc1, args.snifflimit)]

    # determine the most common barcode
    if iseqs:
        barcode_counts = Counter(iseqs)
    else:
        barcode_counts = Counter({None: 0})

    barcodes, counts = list(zip(*barcode_counts.most_common()))

    most_common_bc = barcodes[0]
    try:
        most_common_pct = 100 * float(counts[0]) / sum(counts)
    except ZeroDivisionError:
        most_common_pct = 0
    else:
        if most_common_pct < args.min_pct_assignment:
            msg = 'frequency of most common barcode is less than {}%'.format(
                args.min_pct_assignment)
            if args.strict:
                log.error('Error: ' + msg)
                sys.exit(1)
            else:
                log.warning('Warning: ' + msg)

    log.info('most common barcode: {} ({}/{} = {:.2f}%)'.format(
        most_common_bc, counts[0], sum(counts), most_common_pct))

    if args.barcode_counts:
        # Create a writer using the CSV module
        barcode_counts_writer = csv.writer(args.barcode_counts)
        # Write a header
        barcode_counts_writer.writerow(['barcode', 'diff_most_common', 'count'])
        for bc, count in barcode_counts.most_common():
            barcode_counts_writer.writerow([bc, seqdiff(most_common_bc, bc), count])

    if args.show_counts:
        for bc, count in barcode_counts.most_common():
            print(('{}\t{}\t{}'.format(bc, seqdiff(most_common_bc, bc), count)))
        return None

    ifilterfun = filterfalse if args.invert else filter

    # use seqs2 for --read-counts input-count
    seqs, seqs2 = tee(fastqlite(args.fastq, args.allow_empty))

    filtered = zip_longest(seqs, bc2)

    if args.match_filter:
        filtered = ifilterfun(get_match_filter(most_common_bc), filtered)

    if args.qual_filter:
        filtered = ifilterfun(qual_filter, filtered)

    if args.read_counts:
        filtered, filtered2 = tee(filtered)
        input_count = sum(1 for _ in seqs2)
        output_count = sum(1 for _ in filtered2)
        read_counts_writer = csv.writer(args.read_counts)
        read_counts_writer.writerow([args.outfile.name, input_count, output_count])

    for seq, bc in islice(filtered, args.head):
        assert seq.id == bc.id
        args.outfile.write(as_fastq(seq))

    close_all_files(args)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
