from typing import Tuple

from pycocotb.hdlSimulator import HdlSimulator
from pycocotb.process_utils import OnRisingCallbackLoop

# The constant which means that the agent shouLd wait one time quantum
# before sending a new data over an interface.
NOP = "NOP"
RX = "RX"
TX = "TX"


class AgentBase():
    """
    Base class of agent of interface like in UVM
    driver is used for slave interfaces
    monitor is used for master interfaces

    :ivar ~.intf: interface assigned to this agent
    :ivar ~._enable: flag to enable/disable this agent
    :ivar ~._debugOutput: optional stream where to print debug messages
    """
    # because ohterwise there will be a cycle and python
    # will not be able to deallocate this and sim/intf
    __weakref__ = ["intf", "sim"]

    def __init__(self, sim: HdlSimulator, intf):
        self.intf = intf
        self._enabled = True
        self._debugOutput = None
        self.sim = sim

    def setEnable(self, en):
        self._enabled = en

    def getEnable(self):
        return self._enabled

    def _debug(self, out):
        self._debugOutput = out

    def getDrivers(self):
        """
        Called before simulation to collect all drivers of interfaces
        from this agent
        """
        return [self.driver(), ]

    def getMonitors(self):
        """
        Called before simulation to collect all monitors of interfaces
        from this agent
        """
        return [self.monitor(), ]

    def driver(self):
        """
        Implement this method to drive your interface
        in simulation/verification
        """
        raise NotImplementedError()

    def monitor(self):
        """
        Implement this method to monitor your interface
        in simulation/verification
        """
        raise NotImplementedError()


class AgentWitReset(AgentBase):

    def __init__(self, sim: HdlSimulator, intf, rst: Tuple["RtlSignal", bool]):
        """
        :param rst: tuple (rst signal, rst_negated flag)
        """
        super(AgentWitReset, self).__init__(sim, intf)
        rst, rst_negated = rst
        self.rst = rst
        self.rstOffIn = int(rst_negated)

    def notReset(self):
        if self.rst is None:
            return True

        rstVal = self.rst.read()
        rstVal = int(rstVal)
        return rstVal == self.rstOffIn


class SyncAgentBase(AgentWitReset):
    """
    Agent which runs only monitor/driver function at specified edge of clk
    """
    SELECTED_EDGE_CALLBACK = OnRisingCallbackLoop

    def __init__(self, sim: HdlSimulator,
                 intf,
                 clk: "RtlSignal",
                 rst: Tuple["RtlSignal", bool],
                  wrap_monitor_and_driver_in_edge_callback=True):
        super(SyncAgentBase, self).__init__(
            sim, intf, rst)
        self.clk = clk

        if wrap_monitor_and_driver_in_edge_callback:
            # run monitor, driver only on rising edge of clk
            c = self.SELECTED_EDGE_CALLBACK
            self.monitor = c(sim, self.clk, self.monitor, self.getEnable)
            self.driver = c(sim, self.clk, self.driver, self.getEnable)

    def setEnable_asDriver(self, en: bool):
        self._enabled = en
        self.driver.setEnable(en)

    def setEnable_asMonitor(self, en: bool):
        self._enabled = en
        self.monitor.setEnable(en)

    def getDrivers(self):
        self.setEnable = self.setEnable_asDriver
        return AgentBase.getDrivers(self)

    def getMonitors(self):
        self.setEnable = self.setEnable_asMonitor
        return AgentBase.getMonitors(self)

