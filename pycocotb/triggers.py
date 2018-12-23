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
    """
    Start of evaluation of RTL simulator, in this phase
    only write is allowed
    """
    PRIORITY = PRIORITY_URGENT + 1


class _WriteOnlyToReadOnlyTransition(SimStep):
    """
    RTL simulation performes the evaluation of combinational logic
    """
    PRIORITY = WriteOnly.PRIORITY + 1


class ReadOnly(SimStep):
    """
    Update of combinational logic was performed and now
    it is posible to read values and wait again on WriteOnly to update
    circuit again
    """
    PRIORITY = WriteOnly.PRIORITY + 1


class _CombLogicReevalCheck(SimStep):
    """
    Simulator check if input of combinational logic was altered and
    RTL simulation should be revaluated before evaluation of event
    dependent events
    """
    PRIORITY = ReadOnly.PRIORITY + 1


class CombStable(SimStep):
    """
    Combinational logic is stable and no update update
    of any IO is allowed on this timestamp
    """
    PRIORITY = CombStable.PRIORITY + 1


class AllStable(SimStep):
    """
    All values in circuit are stable for this timestamp
    """
    PRIORITY = CombStable.PRIORITY + 1


class _EndOfStepToNewStepTransition(SimStep):
    """
    Simulation state is set to start of new step
    """
    PRIORITY = AllStable.PRIORITY + 1


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
