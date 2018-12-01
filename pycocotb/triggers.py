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


class Timer(Event):
    """
    Container for wait time of processes

    next activation of process will be now + time
    """

    def __init__(self, time):
        self.time = time

    def __repr__(self):
        return "<Timer %r>" % (self.time)


class ReadOnly(Event):
    pass


class WriteOnly(Event):
    pass
