from pycocotb.triggers import Timer, WaitWriteOnly, WaitCombRead
from pycocotb.process_utils import OnRisingCallbackLoop


def get_clk_driver(clk, clk_period):

    def clk_driver(sim):
        while True:
            yield WaitWriteOnly()
            clk.write(0)

            yield Timer(clk_period // 2)
            yield WaitWriteOnly()

            clk.write(1)
            yield Timer(clk_period // 2)

    return clk_driver


def get_rst_driver(rst, delay):

    def rst_driver(sim):
        yield WaitWriteOnly()
        assert sim.now == 0
        rst.write(1)

        yield Timer(delay)
        assert sim.now == delay
        yield WaitWriteOnly()
        assert sim.now == delay
        rst.write(0)

    return rst_driver


def get_pull_up_driver(sig, delay):

    def pull_up_after(sim):
        yield WaitWriteOnly()
        sig.write(0)

        yield Timer(delay)
        assert sim.now == delay
        yield WaitWriteOnly()
        sig.write(1)

    return pull_up_after


def get_pull_up_driver_with_reset(sig, reset, clk_period):

    def pull_up_after(sim):
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

    return pull_up_after


def get_sync_pull_up_driver_with_reset(sig, clk, rst):

    def init(sim):
        yield WaitWriteOnly()
        sig.write(0)
        assert sim.now == 0

    def pull_up_after(sim):
        exp_t = sim.now
        yield WaitCombRead()
        assert sim.now == exp_t

        if not rst.read():
            yield WaitWriteOnly()
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
        yield WaitCombRead()
        if not rst.read():
            result.append((sim.now, int(sig.read())))

    return OnRisingCallbackLoop(clk, monitorWithClk, lambda: True)

