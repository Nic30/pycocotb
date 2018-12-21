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


class Timer(object):
    """
    Container for wait time of processes

    next activation of process will be now + time
    """

    def __init__(self, time):
        self.time = time

    def __repr__(self):
        return "<Timer %r>" % (self.time)


PRIORITY_URGENT = 0
PRIORITY_NORMAL = PRIORITY_URGENT + 1


class SimStep(object):
    pass


class ReadOnly(SimStep):
    PRIORITY = PRIORITY_NORMAL
    pass


class WriteOnly(SimStep):
    PRIORITY = PRIORITY_NORMAL + 1
    pass
