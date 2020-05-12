from setuptools.py31compat import TemporaryDirectory
import unittest

from pycocotb.agents.peripheral.i2c import I2cAgent
from pycocotb.constants import CLK_PERIOD
from pycocotb.hdlSimulator import HdlSimulator
from pycocotb.tests.common import build_sim


class Tristate():
    """
    Utility which allows access to tri-state signals by Python object property
    """

    def __init__(self, io, name):
        self.i = getattr(io, name + "_i")
        self.o = getattr(io, name + "_o")
        self.t = getattr(io, name + "_t")

    def as_tuple(self):
        return (self.i, self.o, self.t)


class I2C():
    """
    Utility which allows access to I2C signals by Python object property
    """

    def __init__(self, io, name):
        self.scl = Tristate(io, name + "_scl")
        self.sda = Tristate(io, name + "_sda")

    def as_tuple(self):
        return (self.scl.as_tuple(), self.sda.as_tuple())


class I2cAgent_TC(unittest.TestCase):

    def build_I2c_wire(self, build_dir):
        accessible_signals = [
            # (signal_name, read_only, is_signed, type_width)
            ("i_scl_i", 1, 0, 1),
            ("i_scl_o", 0, 0, 1),
            ("i_scl_t", 0, 0, 1),

            ("i_sda_i", 1, 0, 1),
            ("i_sda_o", 0, 0, 1),
            ("i_sda_t", 0, 0, 1),

            ("o_scl_i", 0, 0, 1),
            ("o_scl_o", 1, 0, 1),
            ("o_scl_t", 1, 0, 1),

            ("o_sda_i", 0, 0, 1),
            ("o_sda_o", 1, 0, 1),
            ("o_sda_t", 1, 0, 1),
        ]
        verilog_files = ["I2c_wire.v"]
        sim = build_sim(verilog_files, accessible_signals, self, build_dir, "I2c_wire")
        i, o = I2C(sim.io, "i"), I2C(sim.io, "o")
        return sim, i, o

    def build_I2c_wire_with_agents(self, build_dir):
        rtl_sim, i, o = self.build_I2c_wire(build_dir)
        sim = HdlSimulator(rtl_sim)

        i_ag = I2cAgent(sim, i.as_tuple(), (None, False))
        o_ag = I2cAgent(sim, o.as_tuple(), (None, False))
        procs = [*i_ag.getDrivers(), *o_ag.getMonitors()]
        # because the pullup is already on other side of interface
        o_ag.sda.pullMode = None
        o_ag.scl.pullMode = None

        return sim, i_ag, o_ag, procs

    def test_nop(self):
        # build_dir = "tmp"
        # if True:
        with TemporaryDirectory() as build_dir:
            sim, i_ag, o_ag, procs = self.build_I2c_wire_with_agents(build_dir)
            ref = [0]
            i_ag.bits.extend(ref)

            # sim.rtl_simulator.set_trace_file("I2c_wire.vcd", -1)
            sim.run(10 * CLK_PERIOD, extraProcesses=procs)
            self.assertSequenceEqual(o_ag.bits,
                                     [I2cAgent.START] + [0 for _ in range(10)])

    def test_simple(self):
        # build_dir = "tmp"
        # if True:
        with TemporaryDirectory() as build_dir:
            sim, i_ag, o_ag, procs = self.build_I2c_wire_with_agents(build_dir)

            ref = [1, 0, 0, 1, 1, 1, 0, 1, 0]
            expected = [I2cAgent.START, 1, 0, 0, 1, 1, 1, 0, 1, 0, 0]
            i_ag.bits.extend(ref)

            # sim.rtl_simulator.set_trace_file("I2c_wire.vcd", -1)
            sim.run(10 * CLK_PERIOD, extraProcesses=procs)
            self.assertSequenceEqual(o_ag.bits,
                                     expected)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    #suite.addTest(I2cAgent_TC('test_simple'))
    suite.addTest(unittest.makeSuite(I2cAgent_TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
