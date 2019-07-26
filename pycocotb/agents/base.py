from pycocotb.process_utils import OnRisingCallbackLoop
from pycocotb.hdlSimulator import HdlSimulator

# The constant which means that the agent shouLd wait one time quantum
# before sending a new data over an interface.
NOP = "NOP"


class AgentBase():
    """
    Base class of agent of interface like in UVM
    driver is used for slave interfaces
    monitor is used for master interfaces

    :ivar intf: interface assigned to this agent
    :ivar _enable: flag to enable/disable this agent
    :ivar _debugOutput: optional stream where to print debug messages
    """

    def __init__(self, intf):
        self.intf = intf
        self._enabled = True
        self._debugOutput = None

    def setEnable(self, en, sim):
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
        return [self.driver, ]

    def getMonitors(self):
        """
        Called before simulation to collect all monitors of interfaces
        from this agent
        """
        return [self.monitor, ]

    def driver(self, sim):
        """
        Implement this method to drive your interface
        in simulation/verification
        """
        raise NotImplementedError()

    def monitor(self, sim):
        """
        Implement this method to monitor your interface
        in simulation/verification
        """
        raise NotImplementedError()


class AgentWitReset(AgentBase):

    def __init__(self, intf, rst, rst_negated: bool):
        super(AgentWitReset, self).__init__(intf)

        self.rst = rst
        self.rstOffIn = int(rst_negated)

    def notReset(self, sim: HdlSimulator):
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

    def __init__(self, intf, clk, rst, rst_negated=False):
        super(SyncAgentBase, self).__init__(
            intf, rst, rst_negated=rst_negated)
        self.clk = clk

        # run monitor, driver only on rising edge of clk
        c = self.SELECTED_EDGE_CALLBACK
        self.monitor = c(self.clk, self.monitor, self.getEnable)
        self.driver = c(self.clk, self.driver, self.getEnable)

    def setEnable_asDriver(self, en: bool, sim: HdlSimulator):
        self._enabled = en
        self.driver.setEnable(en, sim)

    def setEnable_asMonitor(self, en: bool, sim: HdlSimulator):
        self._enabled = en
        self.monitor.setEnable(en, sim)

    def getDrivers(self):
        self.setEnable = self.setEnable_asDriver
        return AgentBase.getDrivers(self)

    def getMonitors(self):
        self.setEnable = self.setEnable_asMonitor
        return AgentBase.getMonitors(self)

