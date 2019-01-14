"""
Pitfalls of delta-step based HDL simulators

* Situation
    * RTL simulator which simulates behavior of circuit step by step
    * Simulation environment (=simulator) composed of user specified processes.
        * Simulator can read all signals in RTL simulator
        * Simulator can write and wait for event only on top level signals.

* Problem is how to ensure correct order of operations in RTL simulator
  and in user specified processes which are controlling RTL simulator
  while keeping simulation simple.

    * Requirements of UVM like interface agents.

        * Agents need to be able:

            * Perform combinational loop (e.g. tristate pull-up in I2C)

            * Wait for (before and after) edge of clock signal (e.g. BRAM port)

                * Clock signal can be driven directly by sim.
                  If this is a case synchronization is simple because simulator
                  and user knows when the event happens (before call delta step).

                * If clock signal is generated by circuit it is problematic because
                  value of clock signal is updated in simulation step together
                  with another signal updates. This can result in incorrect
                  event order and special care is required.

                * After clock event is used to signalize that clock cycle
                  has passed and state of interface and it's agent can be updated.
                  This event is triggered on the end of delta step
                  as it can be triggered only once per delta step.

            * Perform combinational loop for clock signals.

                * Value has to be updated in same step.

                    * Problem is that in simulator code some other events
                      may be pending, extra care is required.

        * Agent is full description of interface protocol and should be universal
          and extensible.

    * Combinational loops between simulator and RTL simulator.

        * If only one signal is updated per delta step there is no problem.

        * However if multiple signals signals (especially clock signals)
          are updated in same delta step combinational loop does not
          have to be resolved before some event dependent (e.g. FF) update
          This results in invalid resolution.

            * Updates of combinational logic has to be resolved before update
              of sequential logic.

    * Clock generated by RTL simulator.

        * Output signals from RTL simulator does not have to have
          values which they have when clock event was triggered, solution:

            * Manually add registers in to circuit to hold correct value.

            * Run simulation process which waits on event on specified signal
              exactly in time of the event. Problem is that in this state some
              values can be undefined and read only access is required.

# Simulator delta step:

* (Event names written in capital)

    def delta_step():
        #RTL simulator eval() call
            #while update:                                -|
                #WRITE_ONLY                                | Care for comb. loops
                #READ_ONLY                                 | in sim. agents
                #rerun eval() if write was used            |
                #check for event on signals driven by sim  |  -| Care for sim. driven events
            #COMB_STABLE - read only                      -|
            #for each triggered edge dependent statement block:
                #BEFORE_EDGE(clk) - read only                  -| Care for clock
                #for each start of evaluation                   | dependent agents
                #of event dependent code                        | where clock is generated
                #(clock sig. updated but none of the registers)-| from circuit
        #END_OF_STEP - read only                    -| Final state resolution

# Run of the simulator:
    while True:
        delta_step()
"""

from heapq import heappush, heappop
from typing import Tuple

from pycocotb.triggers import Event, raise_StopSimulation, Timer, \
    StopSimumulation, PRIORITY_URGENT, ReadOnly, \
    WriteOnly, CombStable, AllStable
from inspect import isgenerator


class ReevalRtlEvents(Exception):
    pass


# [TODO] use c++ red-black tree
# internal
class CalendarItem():

    def __init__(self, time: int, priority: int, value):
        """
        :param time: time when this event this list of event should be evoked
        :param priority: priority as described in this file
        """
        self.key = (time, priority)
        self.value = value

    def __lt__(self, other):
        return self.key < other.key

    def __repr__(self):
        return "<CalendarItem %r %r>" % (self.key, self.value)


class RecheckTopEvent(Exception):
    pass


# internal
class SimCalendar():
    """
    Priority queue where key is time and priority
    """

    def __init__(self):
        self._q = []

    def push(self, time: int, priority: int, value):
        item = CalendarItem(time, priority, value)
        heappush(self._q, item)

    def top(self):
        item = self._q[0]
        return (*item.key, item.value)

    def pop(self) -> Tuple[int, int, int, object]:
        item = heappop(self._q)
        return (*item.key, item.value)

    def __repr__(self):
        q = "\n    ".join([repr(i) for i in self._q])
        return "<SimCalendar size:%d %s>" % (len(self._q), q)


# similar to https://github.com/potentialventures/cocotb/blob/master/cocotb/scheduler.py
class HdlSimulator():
    """
    This simulator simulates the communication between circuit simulator
    and simulation processes which are driving the circuit simulation.
    Simulation processes are usually provided by simulation agents or user.

    :ivar now: actual simulation time
    :ivar _events: heap of simulation events and processes
    :ivar rtl_simulator: circuit simulator used for simulation of circuit itself
    """

    def __init__(self, rtl_simulator):
        super(HdlSimulator, self).__init__()
        self.rtl_simulator = rtl_simulator
        self.now = 0
        # container of outputs for every process
        self._events = SimCalendar()
        self._writeOnlyEv = None
        self._readOnlyEv = None
        self._combStableEv = None
        self._allStableEv = None

        schedule = self._events.push
        #def schedule(*args):
        #    assert self.now <= args[0]
        #    print(self.now, "sched:", *args)
        #    self._events.push(*args)
        self.schedule = schedule

    # internal
    def _add_process(self, proc, priority) -> None:
        """
        Schedule process on actual time with specified priority
        """
        self._events.push(self.now, priority, proc)

    def _run_process(self, process, actualPriority):
        """
        :param actualPriority: priority of actually evaluated process
        """
        # run process or activate processes dependent on Event
        for ev in process:
            # if process requires waiting put it back in queue
            if isinstance(ev, Timer):
                if ev.time == 0:
                    continue
                # put process to sleep as required by Timer event
                self.schedule(self.now + ev.time, PRIORITY_URGENT, process)
                break
            elif isinstance(ev, Event):
                ev.applyProcess(self, process)
                break
            elif isgenerator(ev):
                # else this process spotted new process
                # and it has to be put in queue
                self.schedule(self.now, actualPriority, ev)
            else:
                raise NotImplementedError(ev)

    def evalRtlEvents(self, parentPriotiry: int):
        rtl_sim = self.rtl_simulator
        rtl_pending_event_list = rtl_sim._pending_event_list
        if rtl_pending_event_list:
            # proper solution is to put triggered events to sim.
            # calendar with urgent priority  but we evaluate
            # it directly because of performance
            for _process in rtl_pending_event_list:
                if not isgenerator(_process):
                    _process = _process(self)

                self._run_process(_process, parentPriotiry)
            rtl_pending_event_list.clear()

    def run(self, until: int, extraProcesses=[]) -> None:
        """
        Run simulation for a specified time

        :note: Can be used to run simulation again after it ends from time when it ends.
        :note: Simulator restart is performed by new instantiation of the simulator.
        """
        add_proc = self.add_process
        for p in extraProcesses:
            add_proc(p(self))

        assert until >= self.now, (until, self.now)
        if until == self.now:
            return

        next_event = self._events.pop

        WrP = WriteOnly.PRIORITY
        now, priority = (self.now, WrP)
        # add handle to stop simulation
        self.schedule(now + until, PRIORITY_URGENT, raise_StopSimulation(self))

        rtl_sim = self.rtl_simulator

        # state of RTL simulator is beeing updated and updates are pending
        try:
            # for all events
            while True:
                now, priority, process = next_event()
                # print(now, priority, process)
                assert now >= self.now, (now, process)
                rtl_sim._time = self.now = now

                # process is Python generator or Event
                if isinstance(process, Event):
                    for p in process:
                        self._run_process(p, priority)

                    if process.afterCb is not None:
                        process.afterCb()
                else:
                    self._run_process(process, priority)

        except StopSimumulation:
            return

    def waitWriteOnly(self):
        e = self._writeOnlyEv
        if e is None:
            e = self._writeOnlyEv = Event("WriteOnly")
            e.afterCb = self.onAfterWriteOnly
            self.schedule(self.now, WriteOnly.PRIORITY, e)

        return e

    def onAfterWriteOnly(self):
        self._writeOnlyEv = None
        sim = self.rtl_simulator
        s = sim._eval()
        assert s == sim._COMB_UPDATE_DONE
        self.evalRtlEvents(WriteOnly.PRIORITY)
        # spot ReadOnly event without waiting on it
        self.waitReadOnly()

    def waitReadOnly(self):
        e = self._readOnlyEv
        if e is None:
            e = self._readOnlyEv = Event("ReadOnly")
            e.afterCb = self.onAfterReadOnly
            self.schedule(self.now, ReadOnly.PRIORITY, e)

        return e

    def onAfterReadOnly(self):
        self._readOnlyEv = None
        if self._writeOnlyEv is not None:
            # if write in this time stamp is required we have to reevaluate
            # the combinational logic
            self.rtl_simulator._reset_eval()
        self.waitCombStable()

    def waitCombStable(self):
        e = self._combStableEv
        if e is None:
            e = self._combStableEv = Event("CombStable")
            e.afterCb = self.onFinishRtlStep
            self.schedule(self.now, CombStable.PRIORITY, e)

        return e

    def onFinishRtlStep(self):
        self._combStableEv = None
        sim = self.rtl_simulator
        END = sim._END_OF_STEP
        _eval = sim._eval
        while True:
            ret = _eval()
            if sim._pending_event_list:
                self.evalRtlEvents(AllStable.PRIORITY)
            if ret == END:
                break

        self.waitAllStable()

    def waitAllStable(self):
        e = self._allStableEv
        if e is None:
            e = self._allStableEv = Event("AllStable")
            e.afterCb = self.onAfterStep
            self.schedule(self.now, AllStable.PRIORITY, e)

        return AllStable

    def onAfterStep(self):
        self._allStableEv = None
        self.rtl_simulator._set_write_only()

    def add_process(self, proc) -> None:
        """
        Add process to events with default priority on current time
        """
        self._events.push(self.now, WriteOnly.PRIORITY, proc)

