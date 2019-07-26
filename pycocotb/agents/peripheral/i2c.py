from collections import deque
from typing import Tuple

from pycocotb.agents.base import AgentWitReset
from pycocotb.agents.peripheral.tristate import TristateAgent, TristateClkAgent
from pycocotb.triggers import WaitCombStable


TRI_STATE_SIG_T = Tuple["RtlSignal", "RtlSignal", "RtlSignal"] # i, o, t

class I2cAgent(AgentWitReset):
    START = "start"

    def __init__(self, intf: Tuple[TRI_STATE_SIG_T, TRI_STATE_SIG_T], rst, rst_negated: bool):
        """
        :param: intf i2c interface, tuple (scl, sda) = (clock, data),
            sda/sdc are tri-state interfaces represented by i, o, t signals
        """
        AgentWitReset.__init__(self, intf, rst, rst_negated)
        self.bits = deque()
        self.start = True
        self.sda = TristateAgent(intf[1], rst, rst_negated)
        self.sda.collectData = False
        self.sda.selfSynchronization = False

    def startListener(self, sim):
        if self.start:
            self.bits.append(self.START)
            self.start = False

        return
        yield

    def startSender(self, sim):
        if self.start:
            self.sda._write(0, sim)
            self.start = False
        return
        yield

    def getMonitors(self):
        self.scl = TristateClkAgent(
            self.intf[0], self.rst, self.rstOffIn,
            onRisingCallback=self.monitor,
            onFallingCallback=self.startListener
        )
        return (
            *self.sda.getMonitors(),
            *self.scl.getMonitors()
        )

    def getDrivers(self):
        self.scl = TristateClkAgent(
            self.intf[0], self.rst, self.rstOffIn,
            onRisingCallback=self.driver,
            onFallingCallback=self.startSender
        )
        return (
            self.driver,  # initial initialization
            *self.sda.getDrivers(),
            *self.scl.getDrivers()
        )

    def monitor(self, sim):
        # now intf.sdc is rising
        yield WaitCombStable()
        # wait on all agents to update values and on
        # simulator to appply them
        if sim.now > 0 and self.notReset(sim):
            v = self.sda.i.read()
            self.bits.append(v)

    def driver(self, sim):
        # now intf.sdc is rising
        # yield Timer(1)
        # yield WaitCombStable()
        yield from self.sda.driver(sim)
        # now we are after clk
        # prepare data for next clk
        if self.bits:
            b = self.bits.popleft()
            if b == self.START:
                return
            self.sda._write(b, sim)
