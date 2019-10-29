from collections import deque
from typing import Tuple

from pycocotb.agents.base import NOP, SyncAgentBase
from pycocotb.hdlSimulator import HdlSimulator
from pycocotb.triggers import WaitCombStable, WaitWriteOnly, WaitCombRead


class HandshakedAgent(SyncAgentBase):
    """
    Simulation/verification agent for handshaked interfaces
    interface there is onMonitorReady(simulator)
    and onDriverWriteAck(simulator) unimplemented method
    which can be used for interfaces with bi-directional data streams
    """

    def __init__(self, sim: HdlSimulator, intf, clk: "RtlSignal",
                 rst: Tuple["RtlSignal", bool]):
        super(HandshakedAgent, self).__init__(
            sim, intf, clk, rst)
        self.actualData = NOP
        self.data = deque()

        # tmp variables to keep track of last send values to simulation
        self._lastWritten = None
        self._lastRd = None
        self._lastVld = None
        # callbacks
        self._afterRead = None
        #self.driver.pre_init = True
        #self.monitor.pre_init = True

    def setEnable_asDriver(self, en):
        super(HandshakedAgent, self).setEnable_asDriver(en)
        if not en:
            self.set_valid(0)
            self._lastVld = 0

    def setEnable_asMonitor(self, en):
        super(HandshakedAgent, self).setEnable_asMonitor(en)
        if not en:
            self.set_ready(0)
            self._lastRd = 0

    def get_ready(self) -> bool:
        """
        get value of "ready" signal
        """
        raise NotImplementedError("Implement this method to read ready signal on your interface")

    def set_ready(self, val: bool):
        raise NotImplementedError("Implement this method to write ready signal on your interface")

    def get_valid(self):
        """
        get value of "valid" signal, override f.e. when you
        need to use signal with reversed polarity
        """
        raise NotImplementedError("Implement this method to read valid signal on your interface")

    def set_valid(self, val):
        raise NotImplementedError("Implement this method to write valid signal on your interface")

    def get_data(self):
        """extract data from interface"""
        raise NotImplementedError("Implement this method to read data signals on your interface")

    def set_data(self, data):
        """write data to interface"""
        raise NotImplementedError("Implement this method to write data signals on your interface")

    def monitor(self):
        """
        Collect data from interface
        """
        start = self.sim.now
        yield WaitCombRead()
        if not self._enabled:
            return        

        if self.notReset():
            yield WaitWriteOnly()
            if not self._enabled:
                return
            # update rd signal only if required
            if self._lastRd is not 1:
                self.set_ready(1)
                self._lastRd = 1

                # try to run onMonitorReady if there is any
                try:
                    onMonitorReady = self.onMonitorReady
                except AttributeError:
                    onMonitorReady = None

                if onMonitorReady is not None:
                    onMonitorReady()
            else:
                yield WaitCombRead() 
                assert int(self.get_ready()) == self._lastRd, (
                    "Something changed the value of ready withou notifying of this agent"
                    " which is responsible for this",
                    self.sim.now, self.get_ready(), self._lastRd)
                if not self._enabled:
                    return
           
            if not self._enabled:
                return
            # wait for response of master
            yield WaitCombStable()
            if not self._enabled:
                return
            vld = self.get_valid()
            try:
                vld = int(vld)
            except ValueError:
                raise AssertionError(
                    self.sim.now, self.intf,
                    "vld signal is in invalid state")
            if vld:
                # master responded with positive ack, do read data
                d = self.get_data()
                if self._debugOutput is not None:
                    self._debugOutput.write(
                        "%s, read, %d: %r\n" % (
                            self.intf._getFullName(),
                            self.sim.now, d))
                self.data.append(d)
                if self._afterRead is not None:
                    self._afterRead()
        else:
            if self._lastRd is not 0:
                yield WaitWriteOnly()
                # can not receive, say it to masters
                self.set_ready(0)
                self._lastRd = 0
            else:
                assert int(self.get_ready()) == self._lastRd

        assert start == self.sim.now

    def checkIfRdWillBeValid(self):
        yield WaitCombStable()
        rd = self.get_ready()
        try:
            rd = int(rd)
        except ValueError:
            raise AssertionError(self.sim.now, self.intf, "rd signal in invalid state")

    def driver(self):
        """
        Push data to interface

        set vld high and wait on rd in high then pass new data
        """
        start = self.sim.now
        yield WaitWriteOnly()
        if not self._enabled:
            return
        # pop new data if there are not any pending
        if self.actualData is NOP and self.data:
            self.actualData = self.data.popleft()

        doSend = self.actualData is not NOP

        # update data on signals if is required
        if self.actualData is not self._lastWritten:
            if doSend:
                data = self.actualData
            else:
                data = None

            self.set_data(data)
            self._lastWritten = self.actualData

        yield WaitCombRead()
        if not self._enabled:
            return
        en = self.notReset()
        vld = int(en and doSend)
        if self._lastVld is not vld:
            yield WaitWriteOnly()
            self.set_valid(vld)
            self._lastVld = vld

        if not self._enabled:
            # we can not check rd it in this function because we can not wait
            # because we can be reactivated in this same time
            yield self.checkIfRdWillBeValid()
            return

        # wait for response of slave
        yield WaitCombStable()
        if not self._enabled:
            return
        rd = self.get_ready()
        try:
            rd = int(rd)
        except ValueError:
            raise AssertionError(
                self.sim.now, self.intf,
                "rd signal in invalid state")

        if not vld:
            assert start == self.sim.now
            return

        if rd:
            # slave did read data, take new one
            if self._debugOutput is not None:
                self._debugOutput.write("%s, wrote, %d: %r\n" % (
                    self.intf._getFullName(),
                    self.sim.now,
                    self.actualData))

            a = self.actualData
            # pop new data, because actual was read by slave
            if self.data:
                self.actualData = self.data.popleft()
            else:
                self.actualData = NOP

            # try to run onDriverWriteAck if there is any
            onDriverWriteAck = getattr(self, "onDriverWriteAck", None)
            if onDriverWriteAck is not None:
                onDriverWriteAck()

            onDone = getattr(a, "onDone", None)
            if onDone is not None:
                onDone()

        assert start == self.sim.now
