#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from unittest import TestLoader, TextTestRunner, TestSuite

from pycocotb.tests.verilatorCntr_test import VerilatorCntrTC
from pycocotb.tests.verilatorHierarchy_test import VerilatorHierarchyTC
from pycocotb.tests.wire_test import VerilatorWireTC
from pycocotb.tests.verilatorHandshakedWire_test import VerilatorHandshakedWireTC
from pycocotb.tests.i2c_test import I2cAgent_TC


def testSuiteFromTCs(*tcs):
    loader = TestLoader()
    loadedTcs = [loader.loadTestsFromTestCase(tc) for tc in tcs]
    suite = TestSuite(loadedTcs)
    return suite


suite = testSuiteFromTCs(
    # basic tests
    VerilatorCntrTC,
    VerilatorWireTC,
    VerilatorHierarchyTC,
    VerilatorHandshakedWireTC,
    #I2cAgent_TC,
)

if __name__ == '__main__':
    runner = TextTestRunner(verbosity=2)
    runner.run(suite)
