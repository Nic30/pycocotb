import unittest
from tempfile import TemporaryDirectory
from pycocotb.verilator.simulator_gen import generatePythonModuleWrapper, \
    loadPythonCExtensionFromFile, verilatorCompile
from os.path import abspath, dirname, join
from pycocotb.hdlSimulator import HdlSimulator
from pycocotb.triggers import Timer
from pycocotb.constants import CLK_PERIOD
from pycocotb.process_utils import OnRisingCallbackLoop
from pycocotb.agents.rst import PullDownAgent, PullUpAgent
from pycocotb.agents.clk import ClockAgent

VERILOG_SRCS = dirname(abspath(__file__))


def get_clk_driver(clk, clk_period):

    def clk_driver(sim):
        while True:
            yield sim.waitWriteOnly()
            clk.write(0)

            yield Timer(clk_period // 2)
            yield sim.waitWriteOnly()

            clk.write(1)
            yield Timer(clk_period // 2)

    return clk_driver


def get_rst_driver(rst, delay):

    def rst_driver(sim):
        yield sim.waitWriteOnly()
        assert sim.now == 0
        rst.write(1)

        yield Timer(delay)
        assert sim.now == delay
        yield sim.waitWriteOnly()
        assert sim.now == delay
        rst.write(0)

    return rst_driver


def get_pull_up_driver(sig, delay):

    def pull_up_after(sim):
        yield sim.waitWriteOnly()
        sig.write(0)

        yield Timer(delay)
        assert sim.now == delay
        yield sim.waitWriteOnly()
        sig.write(1)

    return pull_up_after


def get_pull_up_driver_with_reset(sig, reset, clk_period):

    def pull_up_after(sim):
        exp_t = 0
        yield sim.waitWriteOnly()
        sig.write(0)
        assert sim.now == exp_t

        while True:
            yield sim.waitReadOnly()
            if not reset.read():
                assert sim.now == exp_t
                yield sim.waitWriteOnly()
                sig.write(1)
                return
            else:
                yield Timer(clk_period)
                exp_t += clk_period

    return pull_up_after


def get_sync_pull_up_driver_with_reset(sig, clk, rst):

    def init(sim):
        yield sim.waitWriteOnly()
        sig.write(0)
        assert sim.now == 0

    def pull_up_after(sim):
        exp_t = sim.now
        yield sim.waitReadOnly()
        assert sim.now == exp_t

        if not rst.read():
            yield sim.waitWriteOnly()
            sig.write(1)
            assert sim.now == exp_t

    return [
        init,
        OnRisingCallbackLoop(clk, pull_up_after, lambda: True),
    ]


def get_sync_sig_monitor(sig, clk, rst, result):

    def monitorWithClk(sim):
        # if clock is specified this function is periodically called every
        # clk tick
        yield sim.waitReadOnly()
        if not rst.read():
            result.append((sim.now, int(sig.read())))

    return OnRisingCallbackLoop(clk, monitorWithClk, lambda: True)


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

        sim_verilog = [join(VERILOG_SRCS, "Cntr.v")]
        verilatorCompile(sim_verilog, build_dir)
        module_file_name = generatePythonModuleWrapper(
            "Cntr", "Cntr",
            build_dir,
            accessible_signals)

        cntr_module = loadPythonCExtensionFromFile(module_file_name, "Cntr")
        cntr_cls = cntr_module.Cntr

        cntrSimInstance = cntr_cls()
        io = cntrSimInstance.io
        for sigName, _, _, _ in accessible_signals:
            sig = getattr(io, sigName)
            self.assertEqual(sig.name, sigName)

        return cntrSimInstance

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

            def data_collector(sim):
                yield Timer(CLK_PERIOD // 2)
                assert sim.now == CLK_PERIOD // 2

                val = io.val
                while True:
                    yield Timer(CLK_PERIOD)
                    yield sim.waitReadOnly()
                    data.append((sim.now, int(val.read())))

            sim = HdlSimulator(rtl_sim)
            # rtl_sim.set_trace_file("cntr.vcd", -1)
            sim.run(CLK_PERIOD * 10.5,
                    extraProcesses=[
                        get_clk_driver(io.clk, CLK_PERIOD),
                        get_rst_driver(io.rst, CLK_PERIOD),
                        get_pull_up_driver(io.en, CLK_PERIOD),
                        data_collector
                        ]
                    )

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
            sim.run(CLK_PERIOD * 10.5,
                    extraProcesses=[
                        get_clk_driver(io.clk, CLK_PERIOD),
                        get_rst_driver(io.rst, CLK_PERIOD),
                        get_pull_up_driver(io.en, CLK_PERIOD),
                        get_sync_sig_monitor(io.val, io.clk, io.rst, data)
                        ]
                    )

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
            sim.run(CLK_PERIOD * 10.5,
                    extraProcesses=[
                        get_clk_driver(io.clk, CLK_PERIOD),
                        get_rst_driver(io.rst, CLK_PERIOD),
                        get_pull_up_driver_with_reset(io.en, io.rst, CLK_PERIOD),
                        get_sync_sig_monitor(io.val, io.clk, io.rst, data)
                        ]
                    )

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
            sim.run(CLK_PERIOD * 10.5,
                    extraProcesses=[
                        get_clk_driver(io.clk, CLK_PERIOD),
                        get_rst_driver(io.rst, CLK_PERIOD),
                        *get_sync_pull_up_driver_with_reset(io.en, io.clk, io.rst),
                        get_sync_sig_monitor(io.val, io.clk, io.rst, data)
                        ]
                    )

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
                *ClockAgent(io.clk).getDrivers(),
                *PullDownAgent(io.rst).getDrivers(),
                *PullUpAgent(io.en, initDelay=CLK_PERIOD).getDrivers(),
                get_sync_sig_monitor(io.val, io.clk, io.rst, data)
            ]
            rtl_sim.set_trace_file(join(build_dir, "cntr.vcd"), -1)
            sim.run(CLK_PERIOD * 10.5, extraProcesses=procs)

            self.assertSequenceEqual(data, REF_DATA)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    #suite.addTest(VerilatorCntrTC('test_sim_normal_agents'))
    suite.addTest(unittest.makeSuite(VerilatorCntrTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
