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

from itertools import islice, tee, repeat
try:
    from itertools import filterfalse, zip_longest
except ImportError:
    from itertools import izip_longest as zip_longest
    from itertools import ifilterfalse as filterfalse
    from itertools import ifilter as filter


from fastalite import fastqlite, Opener

log = logging.getLogger(__name__)

try:
    from . import __version__
except Exception:
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


# def get_match_filter(barcode):
#     """Return a function for filtering a pair of (seq, bc) namedtuple
#     pairs; the function returns True if bc.seq == barcode

#     """

#     def filterfun(pair):
#         seq, bc = pair
#         return str(bc.seq) == barcode

#     return filterfun


def get_match_filter(bcseqs, snifflimit=None):
    """Provides a filter for exact bacode matches.

    * bcseqs - an iterator of Seq namedtuples
    * snifflimit - maximum number of barcodes to count.

    Returns ``(filterfun, counts)``. ``filterfun`` is a function for
    filtering a pair of (seq, bc) namedtuple pairs; the function
    returns True if bc.seq == barcode. ``counts`` is a
    collections.Counter object providing barcode counts.

    Note that ``bcseqs`` is consumed in this function.

    """

    # determine the most common barcode
    counts = Counter(
        [str(seq.seq) for seq in islice(bcseqs, snifflimit)])

    most_common, __ = counts.most_common(1)[0]

    def filterfun(pair):
        seq, bc = pair
        return str(bc.seq) == most_common

    return filterfun, counts


def check_barcode_freqs(barcode_counts, min_pct=0):
    barcodes, counts = list(zip(*barcode_counts.most_common()))
    most_common_bc = barcodes[0]
    most_common_pct = 100 * float(counts[0]) / sum(counts)

    log.info('most common barcode: {} ({}/{} = {:.2f}%)'.format(
        most_common_bc, counts[0], sum(counts), most_common_pct))

    if most_common_pct < min_pct:
        raise ValueError('frequency of most common barcode < {}%'.format(min_pct))


def get_qual_filter2(min_qual, encoding, paired=False):
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


def get_qual_filter(min_qual, encoding):
    """Return a function for filtering a pair of (seq, bc) namedtuple
    pairs. The function returns True if the average barcode quality
    score calculated using the provided encoding method is at least
    min_qual. The function defined for a encoding method
    is specified as ``get_{}_encoding``.  Currently only Sanger phred
    encoding is supported -- see ``get_phred_encoding``.

    """

    encoding = globals()['get_{}_encoding'.format(encoding)]()

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

    match_options = parser.add_argument_group('Barcode matching options')

    match_options.add_argument(
        '--match-filter', action='store_true', default=False,
        help=('filter reads based on exact match to most common barcode '
              '[default: no match filter]'))
    parser.add_argument(
        '--snifflimit', type=int, default=10000, metavar='N',
        help="""read no more than N records from the index file to
        calculate most common barcode [%(default)s]""")
    match_options.add_argument(
        '--min-pct-assignment', type=float, default=90.0, metavar='PERCENT',
        help=("""warn (or fail with an error; see --strict) if the
               most common barcode represents less than PERCENT of the
               total [%(default)s]"""))
    match_options.add_argument(
        '--strict', action='store_true', default=False,
        help=("""fail if conditions of --min-pct-assignment are not met"""))
    match_options.add_argument(
        '-C', '--csv-counts', type=argparse.FileType('w'), metavar='FILE',
        help='tabulate barcode counts and store as a CSV')

    qual_options = parser.add_argument_group('Barcode quality filtering options')

    qual_options.add_argument(
        '--qual-filter', action='store_true', default=False,
        help="""filter reads based on minimum index quality [default:
        no quality filter]""")
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
        level=logging.ERROR if args.quiet else logging.INFO)

    keep = repeat(True)
    for bcfile in args.index:
        bcseqs = fastqlite(bcfile)

        qual_filter = get_qual_filter(args.min_qual, args.encoding)

        # avoid consuming bcseqs while determining most frequent barcode
        bcseqs, _bcseqs = tee(bcseqs, 2)
        matchfun, bccounts = get_match_filter(_bcseqs, args.snifflimit)

        try:
            check_barcode_freqs(bccounts, args.min_pct_assignment)
        except ValueError as err:
            log.error(str(err))
            if args.strict:
                exit(1)

    # if args.csv_counts:
    #     # Create a writer using the CSV module
    #     csv_counts_writer = csv.writer(args.csv_counts)
    #     # Write a header
    #     csv_counts_writer.writerow(['barcode', 'diff_most_common', 'count'])
    #     for bc, count in barcode_counts.most_common():
    #         csv_counts_writer.writerow([bc, seqdiff(most_common_bc, bc), count])

    if not args.fastq:
        log.error('specify a fastq format file to filter using -f/--fastq')
        sys.exit(1)

    ifilterfun = filterfalse if args.invert else filter

    seqs = fastqlite(args.fastq)
    filtered = zip_longest(seqs, bc2)

    if args.match_filter:
        filtered = ifilterfun(get_match_filter(most_common_bc), filtered)

    if args.qual_filter:
        filtered = ifilterfun(qual_filter, filtered)

    for seq, bc in islice(filtered, args.head):
        assert seq.id == bc.id
        args.outfile.write(as_fastq(seq))


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
