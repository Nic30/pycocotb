from pycocotb.hdlSimulator import HdlSimulator
from pycocotb.process_utils import OnRisingCallbackLoop
from pycocotb.triggers import Timer, WaitWriteOnly, WaitCombRead


def get_clk_driver(sim: HdlSimulator, clk, clk_period):
    while True:
        yield WaitWriteOnly()
        clk.write(0)

        yield Timer(clk_period // 2)
        yield WaitWriteOnly()

        clk.write(1)
        yield Timer(clk_period // 2)


def get_rst_driver(sim: HdlSimulator, rst, delay):
    yield WaitWriteOnly()
    assert sim.now == 0
    rst.write(1)

    yield Timer(delay)
    assert sim.now == delay
    yield WaitWriteOnly()
    assert sim.now == delay
    rst.write(0)


def get_pull_up_driver(sim: HdlSimulator, sig, delay):
    yield WaitWriteOnly()
    sig.write(0)

    yield Timer(delay)
    assert sim.now == delay
    yield WaitWriteOnly()
    sig.write(1)


def get_pull_up_driver_with_reset(sim: HdlSimulator, sig, reset, clk_period):
    exp_t = 0
    yield WaitWriteOnly()
    sig.write(0)
    assert sim.now == exp_t

    while True:
        yield WaitCombRead()
        if not reset.read():
            assert sim.now == exp_t
            yield WaitWriteOnly()
            sig.write(1)
            return
        else:
            yield Timer(clk_period)
            exp_t += clk_period


def get_sync_pull_up_driver_with_reset(sim: HdlSimulator, sig, clk, rst):
    # init
    yield WaitWriteOnly()
    sig.write(0)
    assert sim.now == 0

    def pull_up_after():
        exp_t = sim.now
        yield WaitCombRead()
        assert sim.now == exp_t

        if not rst.read():
            yield WaitWriteOnly()
            sig.write(1)
            assert sim.now == exp_t

    yield OnRisingCallbackLoop(sim, clk, pull_up_after, lambda: True)()


def get_sync_sig_monitor(sim: HdlSimulator, sig, clk, rst, result):

    def monitorWithClk():
        # if clock is specified this function is periodically called every
        # clk tick
        yield WaitCombRead()
        if not rst.read():
            result.append((sim.now, int(sig.read())))

    return OnRisingCallbackLoop(sim, clk, monitorWithClk, lambda: True)()

