from sortedcontainers.sortedset import SortedSet
from pycocotb.basic_hdl_simulator.sim_utils import valueHasChanged


class BasicSimProxy():
    """
    Signal proxy which manages the access to a memory in simulation

    :ivar callbacks: list of sim processes which will be waken up if signal value is updated
    :ivar sim: main simulator
    :ivar name: name of property which is this proxy stored in on parent
    :ivar _name: signal name which was used in HDL
    :ivar _dtype: data type of this signal
    :ivar _origin: the object which was this proxy generated from
    :ivar _ag: agent which controlls this proxy
    :ivar parent: parent object
    :ivar def_val: value used for initialization of value (done on sim. startup)
    :ivar val: actual value of signal
    :ivar val_next: place for metainformations about next update
    """
    __slots__ = ["callbacks", "sim", "name", "_name", "parent",
                 "_dtype", "_origin", "_ag",
                 "def_val", "val", "val_next",
                 "simRisingSensProcs", "simFallingSensProcs", "simSensProcs"]

    def __init__(self, sim: "BasicRtlSimulator", parent, name, dtype,
                 def_val=None):
        self.callbacks = []
        self.sim = sim
        self.parent = parent
        self.def_val = def_val
        self.val = dtype.from_py(None)
        self.val_next = None
        # properties used for simplified associations and debug in python
        self.name = name  # physical name
        self._name = name  # logical name
        self._dtype = dtype  # type notation for python
        self._origin = None  # signal object which this proxy substitutes
        self._ag = None  # simulation agent which drive or monitor this signal
        self.simRisingSensProcs = SortedSet()
        self.simFallingSensProcs = SortedSet()
        self.simSensProcs = SortedSet()

    def read(self):
        assert self.sim.read_only_not_write_only
        return self.val

    def write(self, val):
        assert not self.sim.read_only_not_write_only
        val = self._dtype.from_py(val)
        if valueHasChanged(self.val, val):
            self.val = val
            self._propagate_changes()

    def wait(self, cb):
        self.callbacks.append(cb)
        self.sim.signals_checked_for_change.add(cb)

    def _apply_update(self, valUpdater):
        """
        Method called by simulator to update new value for this object
        """
        dirty_flag, new_val = valUpdater(self.val)

        if dirty_flag:
            self.val = new_val
            self._propagate_changes()

    def _propagate_changes(self):
        v = self.val
        sim = self.sim
        log = sim.config.logChange
        if log:
            log(sim.time, self, v)

        log = sim.config.logPropagation
        if log:
            log(sim, self, self.simSensProcs)

        # # run all sensitive processes
        for p in self.simSensProcs:
            sim._add_hdl_proc_to_run(self, p)

        # run write callbacks we have to create new list to allow
        # registering of new call backs in callbacks
        self.sim.pending_event_list.extend(self.callbacks)

        if self.simRisingSensProcs:
            if v.val or not v.vld_mask:
                if log:
                    log(sim, self, self.simRisingSensProcs)
                for p in self.simRisingSensProcs:
                    sim._add_hdl_proc_to_run(self, p)

        if self.simFallingSensProcs:
            if not v.val or not v.vld_mask:
                if log:
                    log(sim, self, self.simFallingSensProcs)
                for p in self.simFallingSensProcs:
                    sim._add_hdl_proc_to_run(self, p)

    def __repr__(self):
        return "<%s %r.%s %r %r>" % (self.__class__.__name__, self.parent,
                                     self.name, self.val, self.val_next)
