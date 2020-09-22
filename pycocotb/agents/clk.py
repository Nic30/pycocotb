from pycocotb.agents.base import AgentBase
from pycocotb.constants import CLK_PERIOD
from pycocotb.hdlSimulator import HdlSimulator
from pycocotb.process_utils import CallbackLoop
from pycocotb.triggers import Timer, WaitWriteOnly, WaitCombRead


class ClockAgent(AgentBase):
    """
    Simulation agent for :class:`hwt.interfaces.std.Clk` interface

    * In driver mode oscillates at frequency specified by period

    * In monitor driver captures tuples (time, nextVal) for each change
        on signal (nextVal is 1/0/None)

    :ivar ~.period: period of signal to generate
    :ivar ~.initWait: time to wait before starting oscillation
    """

    def __init__(self, sim: HdlSimulator, intf: "RtlSignal", period: int=CLK_PERIOD):
        super(ClockAgent, self).__init__(sim, intf)
        assert isinstance(period, int)
        self.period = period
        self.initWait = 0
        self.monitor = CallbackLoop(sim, self.intf, self.monitor, self.getEnable)

    def driver(self):
        assert isinstance(self.period, int)
        assert isinstance(self.initWait, int)
        sig = self.intf
        yield WaitWriteOnly()
        sig.write(0)
        yield Timer(self.initWait)

        while True:
            halfPeriod = self.period // 2

            yield Timer(halfPeriod)
            yield WaitWriteOnly()
            sig.write(1)

            yield Timer(halfPeriod)
            yield WaitWriteOnly()
            sig.write(0)

    def getMonitors(self):
        self.last = (-1, None)
        self.data = []
        return super(ClockAgent, self).getMonitors()

    def monitor(self):
        assert isinstance(self.period, int)
        assert isinstance(self.initWait, int)
        yield WaitCombRead()
        v = self.intf.read()
        try:
            v = int(v)
        except ValueError:
            v = None

        now = self.sim.now
        last = self.last

        _next = (now, v)
        if last[0] == now:
            if last[1] is not v:
                # update last value
                last = (now, v)
                self.last = last
                if self.data:
                    self.data[-1] = last
                else:
                    self.data.append(last)
            else:
                return
        else:
            self.data.append(_next)

        self.last = _next
