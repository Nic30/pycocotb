class StopSimumulation(BaseException):
    """
    Exception raised from handle in simulation to stop simulation
    """
    pass


class Event():
    """
    Simulation event

    Container of processes to wake
    """

    def __init__(self):
        self.process_to_wake = []

    def __iter__(self):
        procs = iter(self.process_to_wake)
        self.process_to_wake = None
        return procs


def raise_StopSimulation(sim):
    """
    Simulation process used to stop simulation
    """
    raise StopSimumulation()
    return
    yield


PRIORITY_URGENT = 0


class SimStep(object):
    pass


class WriteOnly(SimStep):
    PRIORITY = PRIORITY_URGENT + 1
    pass


class ReadOnly(SimStep):
    PRIORITY = WriteOnly.PRIORITY + 1
    pass


class CombStable(SimStep):
    PRIORITY = ReadOnly.PRIORITY + 1
    pass


class AllStable(SimStep):
    PRIORITY = CombStable.PRIORITY + 1
    pass


class Timer():
    """
    Container for wait time of processes

    next activation of process will be now + time
    """

    def __init__(self, time, priority=WriteOnly.PRIORITY):
        self.time = time
        self.priority = priority

    def __repr__(self):
        return "<Timer %r>" % (self.time)
