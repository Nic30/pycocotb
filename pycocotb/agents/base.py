

class AgentBase():
    """
    Base class of agent of interface like in UVM
    driver is used for slave interfaces
    monitor is used for master interfaces

    :ivar intf: interface assigned to this agent
    :ivar enable: flag to enable/disable this agent
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
        return [self.driver]

    def getMonitors(self):
        """
        Called before simulation to collect all monitors of interfaces
        from this agent
        """
        return [self.monitor]

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
