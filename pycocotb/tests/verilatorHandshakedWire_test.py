from tempfile import TemporaryDirectory
import unittest

from pycocotb.agents.clk import ClockAgent
from pycocotb.agents.handshaked import HandshakedAgent
from pycocotb.agents.rst import PullUpAgent
from pycocotb.constants import CLK_PERIOD
from pycocotb.hdlSimulator import HdlSimulator
from pycocotb.tests.common import build_sim
from pycocotb.tests.verilatorHierarchy_test import VerilatorHierarchyTC


class HSAg(HandshakedAgent):

    def set_valid(self, val: bool):
        return self.intf[0].write(val)

    def get_valid(self):
        return self.intf[0].read()

    def get_ready(self):
        return self.intf[1].read()

    def set_ready(self, val: bool):
        self.intf[1].write(val)

    def set_data(self, data):
        self.intf[2].write(data)

    def get_data(self):
        return self.intf[2].read()


def generate_handshaked_agents(sim, io, clk, rst_n):

    din_ag = HSAg(sim, (io.dataIn_vld, io.dataIn_rd, io.dataIn_data),
                  clk, (rst_n, True))
    dout_ag = HSAg(sim, (io.dataOut_vld, io.dataOut_rd, io.dataOut_data),
                   clk, (rst_n, True))

    return din_ag, dout_ag


class VerilatorHandshakedWireTC(unittest.TestCase):
    """
    Tests of Handshaked agent
    """

    def hw_build(self, build_dir):
        """
        Build simulator for HandshakedWire.v in specified dir
        """
        accessible_signals = [
            # (signal_name, read_only, is_signed, type_width)
            ("clk", 0, 0, 1),
            ("rst_n", 0, 0, 1),
            ("dataIn_data", 0, 0, 8),
            ("dataIn_rd", 0, 0, 1),
            ("dataIn_vld", 1, 0, 1),

            ("dataOut_data", 1, 0, 8),
            ("dataOut_rd", 0, 0, 1),
            ("dataOut_vld", 1, 0, 1),
        ]
        verilog_files = ["HandshakedWire.v"]
        return build_sim(verilog_files, accessible_signals, self,
                         build_dir, "HandshakedWire")

    def _test_pass_data(self, initFn):
        # build_dir = "tmp"
        # if True:
        with TemporaryDirectory() as build_dir:
            rtl_sim = self.hw_build(build_dir)
            io = rtl_sim.io
            sim = HdlSimulator(rtl_sim)

            din_ag, dout_ag = generate_handshaked_agents(
                sim, io, io.clk, io.rst_n)

            extra_procs = initFn(sim, din_ag, dout_ag)
            if extra_procs is None:
                extra_procs = []

            proc = [
                *ClockAgent(sim, io.clk, CLK_PERIOD).getDrivers(),
                *PullUpAgent(sim, io.rst_n, CLK_PERIOD).getDrivers(),
                *din_ag.getDrivers(),
                *dout_ag.getMonitors(),
                *extra_procs,
            ]
            sim.run(int(CLK_PERIOD * 20.5), extraProcesses=proc)
            return sim, din_ag, dout_ag

    def test_nop(self):

        def init(sim, din_ag, dout_ag):
            pass

        _, din_ag, dout_ag = self._test_pass_data(init)
        self.assertSequenceEqual(din_ag.data, [])
        self.assertSequenceEqual(dout_ag.data, [])

    def test_simple_data(self):
        ref_data = [1, 2, 3, 4, 5]

        def init(sim, din_ag, dout_ag):
            din_ag.data.extend(ref_data)

        _, din_ag, dout_ag = self._test_pass_data(init)

        self.assertSequenceEqual(din_ag.data, [])
        self.assertSequenceEqual(dout_ag.data, ref_data)

    def test_fifo(self):
        ref_data = [1, 2, 3, 4, 5]

        def init(sim, din_ag, dout_ag):
            # sim.rtl_simulator.set_trace_file("tmp/handshaked_fifo.vcd", -1)
            din_ag.data.extend(ref_data)

        hw_build = self.hw_build

        def hf_build(build_dir):
            return VerilatorHierarchyTC.build_handshaked_fifo(self, build_dir)

        try:
            self.hw_build = hf_build
            _, din_ag, dout_ag = self._test_pass_data(init)
            self.assertSequenceEqual(din_ag.data, [])
            self.assertSequenceEqual(dout_ag.data, ref_data)
        finally:
            self.hw_build = hw_build


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(VerilatorHandshakedWireTC('test_fifo'))
    suite.addTest(unittest.makeSuite(VerilatorHandshakedWireTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
