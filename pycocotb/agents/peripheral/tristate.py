from collections import deque
from typing import Tuple

from pycocotb.agents.base import AgentWitReset, NOP
from pycocotb.agents.clk import DEFAULT_CLOCK
from pycocotb.triggers import Timer, WaitWriteOnly, WaitCombRead, Edge


class TristateAgent(AgentWitReset):

    def __init__(self, intf: Tuple["RtlSignal", "RtlSignal", "RtlSignal"],
                 rst: "RtlSignal", rst_negated: bool):
        """
        :param intf: tuple (i signal, o signal, t signal) as present in tristate interface
        :note: t signal controls if the output should be connected, if 't'=0 the 'o' does not have effect
        """
        super(TristateAgent, self).__init__(intf, rst, rst_negated)
        self.i, self.o, self.t = intf
        self.data = deque()
        # can be (1: pull-up, 0: pull-down, None: disconnected)
        self.pullMode = 1
        self.selfSynchronization = True
        self.collectData = True

    def monitor(self, sim):
        # read in pre-clock-edge
        yield WaitCombRead()
        t = self.t.read()
        o = self.o.read()

        if self.pullMode is not None and sim.now > 0:
            try:
                t = int(t)
            except ValueError:
                raise AssertionError(
                sim.now, self.t, "This mode, this value => ioblock would burn")
            try:
                o = int(o)
            except ValueError:
                raise AssertionError(
                sim.now, self.o, "This mode, this value => ioblock would burn")

            if self.pullMode != o:
                raise AssertionError(
                sim.now, self.o, "This mode, this value => ioblock would burn")

        if t:
            v = o
        else:
            v = self.pullMode
        yield WaitWriteOnly()
        self.i.write(v)
        if self.collectData and sim.now > 0:
            yield WaitCombRead()
            if self.notReset(sim):
                self.data.append(v)

    def getMonitors(self):
        return [self.onTWriteCallback__init, ]

    def onTWriteCallback(self, sim):
        while True:
            yield Edge(self.t, self.o)

            if self.getEnable():
                yield from self.monitor(sim)

    def _write(self, val, sim):
        if val is NOP:
            # control now has slave
            t = 0
            o = self.pullMode
        else:
            # control now has this agent
            t = 1
            o = val

        self.t.write(t)
        self.o.write(o)

    def onTWriteCallback__init(self, sim):
        """
        Process for injecting of this callback loop into simulator
        """
        yield self.onTWriteCallback(sim)

    def driver(self, sim):
        while True:
            yield WaitWriteOnly()
            if self.data:
                o = self.data.popleft()
                if o == NOP:
                    t = 0
                    o = 0
                else:
                    t = 1
                self.o.write(o)
                self.t.write(t)

            if self.selfSynchronization:
                yield Timer(DEFAULT_CLOCK)
            else:
                break


class TristateClkAgent(TristateAgent):

    def __init__(self, intf, rst: "RtlSignal", rst_negated:bool,
                 onRisingCallback=None, onFallingCallback=None):
        super(TristateClkAgent, self).__init__(intf, rst, rst_negated)
        self.onRisingCallback = onRisingCallback
        self.onFallingCallback = onFallingCallback
        self.period = DEFAULT_CLOCK

    def driver(self, sim):
        o = self.o
        high = self.pullMode
        low = not self.pullMode
        halfPeriod = self.period / 2

        yield WaitWriteOnly()
        o.write(low)
        self.t.write(1)
        if high:
            onHigh = self.onRisingCallback
            onLow = self.onFallingCallback
        else:
            onHigh = self.onFallingCallback
            onLow = self.onRisingCallback

        while True:
            yield Timer(halfPeriod)
            yield WaitWriteOnly()
            o.write(high)

            if onHigh:
                yield onHigh(sim)

            yield Timer(halfPeriod)
            yield WaitWriteOnly()
            o.write(low)

            if onLow:
                yield onLow(sim)

    def monitor(self, sim):
        yield WaitCombRead()
        # read in pre-clock-edge
        t = self.t.read()
        o = self.o.read()

        if sim.now > 0 and self.pullMode is not None:
            try:
                t = int(t)
            except ValueError:
                raise AssertionError(
                sim.now, self.t, "This mode, this value => ioblock would burn")
            try:
                o = int(o)
            except ValueError:
                raise AssertionError(
                sim.now, self.o, "This mode, this value => ioblock would burn")
            if self.pullMode != o:
                raise AssertionError(
                sim.now, self.o, "This mode, this value => ioblock would burn")

        if int(t):
            v = o
        else:
            v = self.pullMode

        last = self.i.read()
        try:
            last = int(last)
        except ValueError:
            last = None

        yield WaitWriteOnly()
        self.i.write(v)

        if self.onRisingCallback and (not last) and v:
            yield self.onRisingCallback(sim)

        if self.onFallingCallback and not v and (last or last is None):
            yield self.onFallingCallback(sim)

    def getMonitors(self):
        return [self.onTWriteCallback__init]
