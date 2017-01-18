"""Command line interface to the fastlite package

"""

import sys
import argparse
from fastalite import fastalite, fastqlite, Opener
from . import __version__


def count(seqs):
    for i, seq in enumerate(seqs, 1):
        pass
    print(i)


def names(seqs):
    for seq in seqs:
        print(seq.id)


def lengths(seqs):
    for seq in seqs:
        print('{}\t{}'.format(seq.id, len(seq.seq)))


def main(arguments):

    actions = {'count': count, 'names': names, 'lengths': lengths}

    parser = argparse.ArgumentParser(
        prog='fastalite', description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('action', choices=actions.keys(),
                        help="Action to perform")
    parser.add_argument('infile', help="Input file",
                        metavar='infile.{fasta,fastq}[{.gz,.bz2}]',
                        type=Opener('r'))
    parser.add_argument('-V', '--version', action='version',
                        version=__version__,
                        help='Print the version number and exit')
    args = parser.parse_args(arguments)

    with args.infile as f:
        readfun = fastalite if 'fasta' in f.name else fastqlite
        seqs = readfun(args.infile)
        try:
            fun = actions[args.action]
            fun(seqs)
        except ValueError, err:
            sys.stderr.write('Error: {}\n'.format(str(err)))
            return 1

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
