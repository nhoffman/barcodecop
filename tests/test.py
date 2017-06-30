#!/usr/bin/env python

import sys
import os
from os import path
import inspect
from unittest import TestCase
from cStringIO import StringIO
from itertools import izip_longest

# from fastalite import fastalite, fastqlite, Opener
from barcodecop.barcodecop import main

testfiles = 'testfiles'
barcodes = path.join(testfiles, 'barcodes.fastq.gz')
barcodes_qual = path.join(testfiles, 'barcodes_qual.fastq.gz')
outdir = 'test_output'
most_common = 'TATTACTCTA'
dual1 = path.join(testfiles, 'dual_I1.fastq.gz')
dual2 = path.join(testfiles, 'dual_I2.fastq.gz')
dual_qual1 = path.join(testfiles, 'dual_I1_qual.fastq.gz')
dual_qual2 = path.join(testfiles, 'dual_I2_qual.fastq.gz')
most_common_dual = 'ACTGGTAGGA+TTCTCTCCAG'


class Capturing(list):

    """
    From http://stackoverflow.com/questions/16571150/how-to-capture-stdout-output-from-a-python-function-call
    """

    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self

    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio    # free up some memory
        sys.stdout = self._stdout


def mkoutdir(basedir):
    stacknames = [x[3] for x in inspect.stack()]
    testfun = [name for name in stacknames if name.startswith('test_')][0]
    pth = path.join(basedir, testfun)

    try:
        os.makedirs(pth)
    except OSError:
        pass

    return pth


def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
    args = [iter(iterable)] * n
    return izip_longest(fillvalue=fillvalue, *args)


class TestSingleIndex(TestCase):

    def test_01(self):
        with Capturing() as output:
            # because main() is called in the same global context in
            # each test, '-q' silences logging for all invocations.
            main([barcodes, '-c', '-q'])
        self.assertEqual(output[0].split('\t')[0], most_common)

    def test_02(self):
        # filter barcode file using itself; get back only the most common
        # barcode
        with Capturing() as output:
            main([barcodes, '-f', barcodes, '--match-filter'])
        desc, seqs, __, quals = zip(*grouper(output, 4))
        self.assertSetEqual(set(seqs), {most_common})

    def test_03(self):
        # --head returns the specified number of records
        with Capturing() as output:
            main([barcodes, '-f', barcodes, '--head', '10'])
        desc, seqs, __, quals = zip(*grouper(output, 4))
        self.assertEqual(len(seqs), 10)

    def test_04(self):
        # --invert option removes all instances of the most common bc
        with Capturing() as output:
            main([barcodes, '-f', barcodes, '--invert', '--match-filter'])
        desc, seqs, __, quals = zip(*grouper(output, 4))
        self.assertNotIn(most_common, set(seqs))

    def test_05(self):
        # test warning when recovery is below --min-pct-assignment
        with Capturing() as output:
            main([barcodes, '-f', barcodes, '--min-pct-assignment', '100'])

    def test_06(self):
        # test error with --strict
        with Capturing() as output:
            self.assertRaises(
                SystemExit,
                main,
                [barcodes, '-f', barcodes, '--min-pct-assignment', '100', '--strict'])

    def test_qual_01(self):
        # test quality filtering with defaults
        with Capturing() as output:
            main([barcodes_qual, '-f', barcodes_qual, '--qual-filter'])
        desc, seqs, __, quals = zip(*grouper(output, 4))
        self.assertEqual(len(seqs), 4)

    def test_qual_02(self):
        # test quality filtering with reduced threshold
        with Capturing() as output:
            main(
                [barcodes_qual, '-f', barcodes_qual, '--qual-filter', '-p', '2'])
        desc, seqs, __, quals = zip(*grouper(output, 4))
        self.assertEqual(len(seqs), 5)

    # TODO: test non-default offset, but will need sequences with the
    # appropriate encoding

    # def test_qual_03(self):
    #     # test quality filtering with modified offset
    #     with Capturing() as output:
    #         main(
    #             [barcodes_qual,
    #              '-f',
    #              barcodes_qual,
    #              '--qual-filter',
    #              '-p',
    #              '1',
    #              '--qual-offset',
    #              '34'])
    #     desc, seqs, __, quals = zip(*grouper(output, 4))
    #     self.assertEqual(len(seqs), 5)


class TestDualIndex(TestCase):

    def test_01(self):
        with Capturing() as output:
            # because main() is called in the same global context in
            # each test, '-q' silences logging for all invocations.
            main([dual1, dual2, '-c'])
        self.assertEqual(output[0].split('\t')[0], most_common_dual)

    def test_02(self):
        # filter barcode file using itself; get back only the most common
        # barcode
        with Capturing() as output:
            main([dual1, dual2, '-f', dual1, '--match-filter'])
        desc, seqs, __, quals = zip(*grouper(output, 4))
        self.assertSetEqual(set(seqs), {most_common_dual.split('+')[0]})

    def test_qual_dual(self):
        # test quality filtering with defaults
        with Capturing() as output:
            main([dual_qual1, dual_qual2, '-f', dual_qual1, '--qual-filter'])
        desc, seqs, __, quals = zip(*grouper(output, 4))
        self.assertEqual(len(seqs), 5)
