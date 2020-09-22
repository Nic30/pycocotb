from pycocotb.simCalendar import DONE


class Event():
    """
    Simulation event

    Container of processes to wake

    :param process_to_wake: list of sim. processes (generator instances)
        to wake when this event is triggered
    """
    __slots__ = ["debug_name", "process_to_wake"]

    def __init__(self, debug_name=None):
        self.debug_name = debug_name
        self.process_to_wake = []

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


class Action():

    def applyProcess(self, sim, process):
        raise NotImplementedError()


# [TODO] RisingEdge/FallingEdge with support in c++ code
class Edge(Action):
    """
    :note: if multiple signals specified the process will be triggered on first
        edge on any signal, once at most
    """

    def __init__(self, *signals: "RtlSignal"):
        self.signals = signals

    def applyProcess(self, sim, process):
        if len(self.signals) > 1:

            def wrap():
                """
                Because we need to wake process only once
                and after ignore wake potentially caused by edges on other signals
                """
                yield process

            p = wrap()
        else:
            p = process

        for s in self.signals:
            s.wait(p)

        return False


class Timer(Action):
    """
    Container for wait time of processes

    next activation of process will be now + time
    """

    def __init__(self, time: int):
        assert isinstance(time, int)
        self.time = time

    def applyProcess(self, sim, process):
        sim._schedule_proc(sim.now + self.time, process)
        # return false to notify that the evaluation should be paused
        return False

    def __repr__(self):
        return "<Timer %r>" % (self.time)


class WaitWriteOnly(Action):

    def applyProcess(self, sim, process):
        t = sim._current_time_slot
        ev_list = t.write_only
        if ev_list is None:
            ev_list = t.write_only = []
        elif ev_list is DONE:
            raise AssertionError("Can not write in this time slot any more",
                                 sim.now, process, sim._current_time_slot)
        ev_list.append(process)
        return False


class WaitCombRead(Action):

    def applyProcess(self, sim, process):
        t = sim._current_time_slot
        ev_list = t.comb_read
        if ev_list is None:
            ev_list = t.comb_read = []
        elif ev_list is DONE:
            # use later read only event as the condition is satisfied
            ev_list = sim._current_event_list
        ev_list.append(process)
        return False


class WaitCombStable(Action):

    def applyProcess(self, sim, process):
        t = sim._current_time_slot
        ev_list = t.comb_stable
        if ev_list is None:
            ev_list = t.comb_stable = []
        elif ev_list is DONE:
            # use later read only event as the condition is satisfied
            ev_list = sim._current_event_list

        ev_list.append(process)
        return False


class WaitTimeslotEnd(Action):

    def applyProcess(self, sim, process):
        t = sim._current_time_slot
        ev_list = t.timeslot_end
        if ev_list is None:
            ev_list = t.timeslot_end = []
        elif ev_list == DONE:
            ev_list = sim._current_event_list
        ev_list.append(process)
        return False
