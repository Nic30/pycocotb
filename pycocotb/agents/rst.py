from pycocotb.agents.base import AgentBase
from pycocotb.constants import CLK_PERIOD
from pycocotb.hdlSimulator import HdlSimulator
from pycocotb.triggers import Timer, WaitWriteOnly


class PullUpAgent(AgentBase):
    """
    After specified time value of the signal is set to 1
    :note: usually used for negated reset
    """

    def __init__(self, sim: HdlSimulator, intf: "RtlSignal", initDelay=int(0.6 * CLK_PERIOD)):
        super(PullUpAgent, self).__init__(sim, intf)
        assert isinstance(initDelay, int)
        self.initDelay = initDelay
        self.data = []

    def driver(self):
        sig = self.intf
        yield WaitWriteOnly()
        sig.write(0)
        yield Timer(self.initDelay)
        yield WaitWriteOnly()
        sig.write(1)


class PullDownAgent(AgentBase):
    """
    After specified time value of the signal is set to 0
    :note: usually used for reset
    """

    def __init__(self, sim: HdlSimulator, intf: "RtlSignal", initDelay=int(0.6 * CLK_PERIOD)):
        super(PullDownAgent, self).__init__(sim, intf)
        assert isinstance(initDelay, int)
        self.initDelay = initDelay
        self.data = []

    def driver(self):
        sig = self.intf
        yield WaitWriteOnly()
        sig.write(1)
        yield Timer(self.initDelay)
        yield WaitWriteOnly()
        sig.write(0)
