import unittest
from tempfile import TemporaryDirectory
from pycocotb.verilator.simulator_gen import generatePythonModuleWrapper, \
    loadPythonCExtensionFromFile, verilatorCompile
from os.path import abspath, dirname, join
from pycocotb.hdlSimulator import HdlSimulator
from pycocotb.constants import CLK_PERIOD
from pycocotb.triggers import Timer

VERILOG_SRCS = dirname(abspath(__file__))


class VerilatorWireTC(unittest.TestCase):
    """
    Simple test of verilator simulation wrapper functionality
    """

    def build_sim(self, build_dir, DW, top_name):
        accessible_signals = [
            # (signal_name, read_only, is_signed, type_width)
            ("inp", 0, 0, DW),
            ("outp", 1, 0, DW),
        ]

        sim_verilog = [join(VERILOG_SRCS, top_name + ".v")]
        verilatorCompile(sim_verilog, build_dir)
        module_file_name = generatePythonModuleWrapper(
            top_name, top_name,
            build_dir,
            accessible_signals)

        sim_module =
         loadPythonCExtensionFromFile(module_file_name, top_name)
        sim_cls = getattr(sim_module, top_name)

        simInstance = sim_cls()
        io = simInstance.io
        for sigName, _, _, _ in accessible_signals:
            sig = getattr(io, sigName)
            self.assertEqual(sig.name, sigName)

        return simInstance

    def _test_sim_wire(self, DW, test_data):
        """
        Clock dependency on clk
            * monitor of val
        Simulation step restart due write after reset read
        """
        # build_dir = "tmp"
        # if True:
        with TemporaryDirectory() as build_dir:
            rtl_sim = self.build_sim(build_dir, DW, "wire%d" % DW)
            io = rtl_sim.io
            sim = HdlSimulator(rtl_sim)

            readed = []
            def data_collect(sim):
                for d_ref in test_data:
                    yield sim.waitReadOnly()
                    d = io.outp.read()
                    d = int(d)
                    readed.append(d)
                    self.assertEqual(d, d_ref)
                    yield Timer(CLK_PERIOD)

            def data_feed(sim):
                for d in test_data:
                    yield sim.waitWriteOnly()
                    io.inp.write(d)
                    yield Timer(CLK_PERIOD)

            #rtl_sim.set_trace_file("wire%d.vcd" % DW, -1)
            sim.run(CLK_PERIOD * (len(test_data) + 0.5),
                    extraProcesses=[
                        data_collect,
                        data_feed
                        ]
                    )
            self.assertEqual(len(readed), len(test_data))

    def test_wire2(self):
        data = [1, 2, 3, 0, 2, 1, 2, 0, 2]
        self._test_sim_wire(2, data)

    def test_wire64(self):
        data = [1 << x for x in range(63)]
        self._test_sim_wire(64, data)

    def test_wire128(self):
        data = [1 << x for x in range(127)]
        self._test_sim_wire(128, data)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(VerilatorWireTC('test_wire64'))
    suite.addTest(unittest.makeSuite(VerilatorWireTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
