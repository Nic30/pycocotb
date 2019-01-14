

class Event():
    """
    Simulation event

    Container of processes to wake

    :param process_to_wake: list of sim. processes (generator instances)
        to wake when this event is triggered

    :param afterCb: callback function which is called after this event is resolved
    """

    def __init__(self, debug_name=None):
        self.debug_name = debug_name
        self.process_to_wake = []
        self.afterCb = None

    def __iter__(self):
        return iter(self.process_to_wake)

    def destroy(self):
        self.process_to_wake = None

    def applyProcess(self, sim, process):
        self.process_to_wake.append(process)

    def __repr__(self):
        if self.debug_name is None:
            return super(Event, self).__repr__()
        else:
            return "<Event {} {:#018x}>".format(self.debug_name, id(self))


class Edge(Event):
    def __init__(self, signal: "RtlSignal"):
        self.signal = signal

    def applyProcess(self, sim, process):
        self.signal.wait(process)


# [TODO] RisingEdge/FallingEdge with support in c++ code


class StopSimumulation(BaseException):
    """
    Exception raised from handle in simulation to stop simulation
    """
    pass


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


class ReadOnly(SimStep):
    """
    Update of combinational logic was performed and now
    it is possible to read values and wait again on WriteOnly to update
    circuit again

    After this RTL simulation step is restarted if some process requires to write again
    """
    PRIORITY = WriteOnly.PRIORITY


class CombStable(SimStep):
    """
    Combinational logic is stable and no update update
    of any IO is allowed on this time stamp
    """
    PRIORITY = ReadOnly.PRIORITY + 1


class AllStable(SimStep):
    """
    All values in circuit are stable for this time stamp

    After this simulation time will be updated and new delta step will begin
    """
    PRIORITY = CombStable.PRIORITY + 1


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
