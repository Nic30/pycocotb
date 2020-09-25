from os.path import join
from tempfile import TemporaryDirectory
import unittest

from pycocotb.agents.clk import ClockAgent
from pycocotb.agents.rst import PullDownAgent, PullUpAgent
from pycocotb.constants import CLK_PERIOD
from pycocotb.hdlSimulator import HdlSimulator
from pycocotb.tests.common import build_sim
from pycocotb.tests.example_agents import get_clk_driver, get_rst_driver, \
    get_pull_up_driver, get_sync_sig_monitor, get_pull_up_driver_with_reset, \
    get_sync_pull_up_driver_with_reset
from pycocotb.triggers import Timer, WaitCombStable


REF_DATA = [
    (15000, 0),
    (25000, 1),
    (35000, 2),
    (45000, 3),
    (55000, 0),
    (65000, 1),
    (75000, 2),
    (85000, 3),
    (95000, 0)
]


class VerilatorCntrTC(unittest.TestCase):
    """
    Simple test of verilator simulation wrapper functionality
    """

    def cntr_build(self, build_dir):
        """
        Build simulator for Cntr.v in specified dir
        """
        accessible_signals = [
            # (signal_name, read_only, is_signed, type_width)
            ("clk", 0, 0, 1),
            ("en", 0, 0, 1),
            ("rst", 0, 0, 1),
            ("val", 1, 0, 2),
        ]
        verilog_files = ["Cntr.v"]
        return build_sim(verilog_files, accessible_signals, self, build_dir, "Cntr")

    def test_dual_build(self):
        """
        Test if simulation doe not interfere between each other
        """
        with TemporaryDirectory() as build_dir0, TemporaryDirectory() as build_dir1:
            sim0 = self.cntr_build(build_dir0)
            sim1 = self.cntr_build(build_dir1)
            self.assertIsNot(sim0, sim1)

    def test_sim_cntr(self):
        """
        Time synchronized monitors (val) and drivers (clk, rst, en)
        """
        # build_dir = "tmp"
        # if True:
        with TemporaryDirectory() as build_dir:
            rtl_sim = self.cntr_build(build_dir)
            io = rtl_sim.io
            data = []

            def data_collector():
                yield Timer(CLK_PERIOD // 2)
                assert sim.now == CLK_PERIOD // 2

                val = io.val
                while True:
                    yield Timer(CLK_PERIOD)
                    yield WaitCombStable()
                    data.append((sim.now, int(val.read())))

            sim = HdlSimulator(rtl_sim)
            # rtl_sim.set_trace_file("cntr.vcd", -1)
            procs = [
                get_clk_driver(sim, io.clk, CLK_PERIOD),
                get_rst_driver(sim, io.rst, CLK_PERIOD),
                get_pull_up_driver(sim, io.en, CLK_PERIOD),
                data_collector()
            ]
            sim.run(int(CLK_PERIOD * 10.5), extraProcesses=procs)

            self.assertSequenceEqual(data, REF_DATA)

    def test_sim_cntr2(self):
        """
        Clock dependency on clk
            * monitor of val
        Simulation step restart due write after reset read
        """
        # build_dir = "tmp"
        # if True:
        with TemporaryDirectory() as build_dir:
            rtl_sim = self.cntr_build(build_dir)
            io = rtl_sim.io
            sim = HdlSimulator(rtl_sim)
            data = []

            # rtl_sim.set_trace_file("cntr.vcd", -1)
            procs = [
                get_clk_driver(sim, io.clk, CLK_PERIOD),
                get_rst_driver(sim, io.rst, CLK_PERIOD),
                get_pull_up_driver(sim, io.en, CLK_PERIOD),
                get_sync_sig_monitor(sim, io.val, io.clk, io.rst, data)
            ]
            sim.run(int(CLK_PERIOD * 10.5), extraProcesses=procs)

            self.assertSequenceEqual(data, REF_DATA)

    def test_sim_cntr_pull_up_reset(self):
        """
        Clock dependency on clk
            * monitor of val
        Simulation step restart due write after reset read
        """
        # build_dir = "tmp"
        # if True:
        with TemporaryDirectory() as build_dir:
            rtl_sim = self.cntr_build(build_dir)
            io = rtl_sim.io
            data = []

            sim = HdlSimulator(rtl_sim)
            # rtl_sim.set_trace_file("cntr.vcd", -1)
            proc = [
                get_clk_driver(sim, io.clk, CLK_PERIOD),
                get_rst_driver(sim, io.rst, CLK_PERIOD),
                get_pull_up_driver_with_reset(sim, io.en, io.rst, CLK_PERIOD),
                get_sync_sig_monitor(sim, io.val, io.clk, io.rst, data)
            ]
            sim.run(int(CLK_PERIOD * 10.5), extraProcesses=proc)

            self.assertSequenceEqual(data, REF_DATA)

    def test_sim_cntr_sync_pull_up_reset(self):
        """
        Clock dependency on clk
            * driver of en
            * monitor of val
        Simulation step restart due write after reset read
        """
        # build_dir = "tmp"
        # if True:
        with TemporaryDirectory() as build_dir:
            rtl_sim = self.cntr_build(build_dir)
            io = rtl_sim.io
            data = []

            sim = HdlSimulator(rtl_sim)
            # rtl_sim.set_trace_file(join(build_dir, "cntr.vcd"), -1)
            proc = [
                get_clk_driver(sim, io.clk, CLK_PERIOD),
                get_rst_driver(sim, io.rst, CLK_PERIOD),
                get_sync_pull_up_driver_with_reset(sim, io.en, io.clk, io.rst),
                get_sync_sig_monitor(sim, io.val, io.clk, io.rst, data)
            ]
            sim.run(int(CLK_PERIOD * 10.5), extraProcesses=proc)

            self.assertSequenceEqual(data, REF_DATA)

    def test_sim_normal_agents(self):
        # build_dir = "tmp"
        # if True:
        with TemporaryDirectory() as build_dir:
            rtl_sim = self.cntr_build(build_dir)
            io = rtl_sim.io
            sim = HdlSimulator(rtl_sim)
            data = []
            procs = [
                *ClockAgent(sim, io.clk).getDrivers(),
                *PullDownAgent(sim, io.rst).getDrivers(),
                *PullUpAgent(sim, io.en, initDelay=CLK_PERIOD).getDrivers(),
                get_sync_sig_monitor(sim, io.val, io.clk, io.rst, data)
            ]
            rtl_sim.set_trace_file(join(build_dir, "cntr.vcd"), -1)
            sim.run(int(CLK_PERIOD * 10.5), extraProcesses=procs)

            self.assertSequenceEqual(data, REF_DATA)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(VerilatorCntrTC('test_sim_cntr_sync_pull_up_reset'))
    suite.addTest(unittest.makeSuite(VerilatorCntrTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
