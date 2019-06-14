from tempfile import TemporaryDirectory
import unittest

from pycocotb.agents.clk import ClockAgent
from pycocotb.agents.rst import PullUpAgent
from pycocotb.constants import CLK_PERIOD
from pycocotb.hdlSimulator import HdlSimulator
from pycocotb.tests.common import build_sim
from pycocotb.triggers import Timer
from pycocotb.agents.handshaked import HandshakedAgent
from pycocotb.tests.verilatorHierarchy_test import VerilatorHierarchyTC


def generate_handshaked_agents(io, clk, rst_n):

    class DataInAg(HandshakedAgent):

        def setValid(self, val: bool):
            return io.dataIn_vld.write(val)

        def getReady(self):
            return io.dataIn_rd.read()

        def setData(self, sim, data):
            io.dataIn_data.write(data)

    class DataOutAg(HandshakedAgent):

        def getValid(self):
            return io.dataOut_vld.read()

        def getData(self, sim):
            return io.dataOut_data.read()

        def setReady(self, val:bool):
            io.dataOut_rd.write(val)

    din_ag = DataInAg(None, clk, rst_n, rst_negated=True)
    dout_ag = DataOutAg(None, clk, rst_n, rst_negated=True)

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
        return build_sim(verilog_files, accessible_signals, self, build_dir, "HandshakedWire")

    def _test_pass_data(self, initFn, checkFn):
        # build_dir = "tmp"
        # if True:
        with TemporaryDirectory() as build_dir:
            rtl_sim = self.hw_build(build_dir)
            io = rtl_sim.io
            din_ag, dout_ag = generate_handshaked_agents(io, io.clk, io.rst_n)

            sim = HdlSimulator(rtl_sim)
            # rtl_sim.set_trace_file("handshaked_fifo.vcd", -1)
            extra_procs = initFn(sim, din_ag, dout_ag)
            if extra_procs is None:
                extra_procs = []
            sim.run(CLK_PERIOD * 20.5,
                    extraProcesses=[
                        *ClockAgent(io.clk, CLK_PERIOD).getDrivers(),
                        *PullUpAgent(io.rst_n, CLK_PERIOD).getDrivers(),
                        *din_ag.getDrivers(),
                        *dout_ag.getMonitors(),
                        *extra_procs,
                        ]
                    )
            checkFn(sim, din_ag, dout_ag)

    def test_nop(self):

        def init(sim, din_ag, dout_ag):
            pass

        def check(sim, din_ag, dout_ag):
            self.assertSequenceEqual(din_ag.data, [])
            self.assertSequenceEqual(dout_ag.data, [])

        self._test_pass_data(init, check)

    def test_simple_data(self):
        ref_data = [1, 2, 3, 4, 5]

        def init(sim, din_ag, dout_ag):
            din_ag.data.extend(ref_data)

        def check(sim, din_ag, dout_ag):
            self.assertSequenceEqual(din_ag.data, [])
            self.assertSequenceEqual(dout_ag.data, ref_data)

        self._test_pass_data(init, check)

    # def test_fifo(self):
    #     ref_data = [1, 2, 3, 4, 5]
    #
    #     def init(sim, din_ag, dout_ag):
    #         din_ag.data.extend(ref_data)
    #
    #     def check(sim, din_ag, dout_ag):
    #         self.assertSequenceEqual(din_ag.data, [])
    #         self.assertSequenceEqual(dout_ag.data, ref_data)
    #
    #     hw_build = self.hw_build
    #     def hf_build(build_dir):
    #         return VerilatorHierarchyTC.build_handshaked_fifo(self, build_dir)
    #     try:
    #         self.hw_build = hf_build
    #         self._test_pass_data(init, check)
    #     finally:
    #         self.hw_build = hw_build
    #

if __name__ == "__main__":
    suite = unittest.TestSuite()
    suite.addTest(VerilatorHandshakedWireTC('test_fifo'))
    # suite.addTest(unittest.makeSuite(VerilatorHandshakedWireTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
