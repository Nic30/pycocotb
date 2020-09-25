from tempfile import TemporaryDirectory
import unittest

from pycocotb.constants import CLK_PERIOD
from pycocotb.hdlSimulator import HdlSimulator
from pycocotb.tests.common import build_sim
from pycocotb.triggers import WaitCombStable


class VerilatorHierarchyTC(unittest.TestCase):
    """
    Simple test of verilator simulation wrapper access on multiple hierarchy levels
    """

    def build_handshaked_fifo(self, build_dir):
        DATA_WIDTH = 8
        accessible_signals = [
            # (signal_name, read_only, is_signed, type_width)
            ("clk", 0, 0, 1),
            ("dataIn_data", 0, 0, DATA_WIDTH),
            ("dataIn_rd", 1, 0, 1),
            ("dataIn_vld", 0, 0, 1),
            ("dataOut_data", 1, 0, DATA_WIDTH),
            ("dataOut_rd", 0, 0, 1),
            ("dataOut_vld", 1, 0, 1),
            ("rst_n", 0, 0, 1),
            ("size", 1, 0, 3),

            # (("fifo_inst", "clk"), 1, 0, 1),
            # (("fifo_inst", "dataIn_data"), 1, 0, DATA_WIDTH),
            # (("fifo_inst", "dataIn_wait"), 1, 0, 1),
            # (("fifo_inst", "dataIn_en"), 1, 0, 1),
            # (("fifo_inst", "dataOut_data"), 1, 0, DATA_WIDTH),
            # (("fifo_inst", "dataOut_wait"), 1, 0, 1),
            # (("fifo_inst", "dataOut_en"), 1, 0, 1),
            # (("fifo_inst", "rst_n"), 0, 1, 1),
            # (("fifo_inst", "size"), 1, 1, 3),
            (("fifo_inst", "memory"), 1, 0, [3, DATA_WIDTH]),
            (("fifo_inst", "fifo_read"), 1, 0, 1),
            (("fifo_inst", "fifo_write"), 1, 0, 1),
        ]
        files = ["fifo.v", "HandshakedFifo.v"]
        return build_sim(files, accessible_signals, self, build_dir, "HandshakedFifo")

    def test_sim_HandshakedFifo(self):
        # build_dir = "tmp"
        # if True:
        with TemporaryDirectory() as build_dir:
            rtl_sim = self.build_handshaked_fifo(build_dir)
            io = rtl_sim.io
            sim = HdlSimulator(rtl_sim)

            def check_if_can_read():
                yield WaitCombStable()
                assert(len(io.fifo_inst.memory) == 3)
                item0 = io.fifo_inst.memory[0]
                item0.read()
                for i in io.fifo_inst.memory:
                    i.read()

            sim.run(int(CLK_PERIOD * 10.5),
                    extraProcesses=[
                        check_if_can_read()
                    ]
            )


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(VerilatorWireTC('test_wire64'))
    suite.addTest(unittest.makeSuite(VerilatorHierarchyTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
