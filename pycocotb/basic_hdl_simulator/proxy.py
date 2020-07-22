from pyMathBitPrecise.array3t import Array3t
from pyMathBitPrecise.bits3t import Bits3t
from pycocotb.basic_hdl_simulator.sim_utils import valueHasChanged


class BasicRtlSimProxy():
    """
    Signal proxy which manages the access to a memory in simulation

    :ivar ~.callbacks: list of sim processes which will be waken up if signal value is updated
    :ivar ~.sim: main simulator
    :ivar ~.name: name of property which is this proxy stored in on parent
    :ivar ~._name: signal name which was used in HDL
    :ivar ~._dtype: data type of this signal
    :ivar ~._origin: the object which was this proxy generated from
    :ivar ~._ag: agent which controlls this proxy
    :ivar ~.parent: parent object
    :ivar ~.def_val: value used for initialization of value (done on sim. startup)
    :ivar ~.val: actual value of signal
    :ivar ~.val_next: place for metainformations about next update
    """
    __slots__ = ["callbacks", "sim", "name", "_name", "parent",
                 "_dtype", "_origin", "_ag",
                 "def_val", "val", "val_next",
                 "simRisingSensProcs", "simFallingSensProcs", "simSensProcs"]
    BIT_t = Bits3t(1, False)

    def __init__(self, sim: "BasicRtlSimulator", parent, name, dtype, def_val):
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
        self.simRisingSensProcs = set()
        self.simFallingSensProcs = set()
        self.simSensProcs = set()

    def init_def_val(self, *args, **kwargs):
        self.def_val = self._dtype.from_py(*args, **kwargs)
        return self

    def read(self):
        assert self.sim.read_only_not_write_only
        return self.val.__copy__()

    def write(self, val):
        assert not self.sim.read_only_not_write_only
        t = getattr(val, "_dtype", None)
        if t is None:
            val = self._dtype.from_py(val)
        else:
            val = self._dtype.from_py(
                val.val,
                min(val.vld_mask,
                    self._dtype.all_mask())
            )
        if valueHasChanged(self.val, val):
            self.val = val
            self._propagate_changes(None)

    def wait(self, cb):
        self.callbacks.append(cb)
        self.sim.signals_checked_for_change.add(cb)

    def _apply_update(self, valUpdater):
        """
        Method called by simulator to update new value for this object
        """
        dirty_flag, new_val = valUpdater(self.val)
        assert new_val._dtype == self._dtype, (self, self.sim.time, new_val._dtype, self._dtype)
        if dirty_flag:
            self.val = new_val
            self._propagate_changes(valUpdater)

    def _propagate_changes(self, valUpdater):
        v = self.val
        sim = self.sim
        sim._updated_in_this_step.add(self)
        log = sim.logChange
        if log:
            log(sim.time, self, v, valUpdater)

        log = sim.logPropagation
        if log:
            log(sim, self, self.simSensProcs)

        # # run all sensitive processes
        for p in self.simSensProcs:
            sim._add_hdl_proc_to_run(self, p)

        # run write callbacks we have to create new list to allow
        # registering of new call backs in callbacks
        self.sim.pending_event_list.extend(self.callbacks)
        self.callbacks.clear()

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

    def _onRisingEdge(self):
        v = self.val
        is_rising = self in self.sim._updated_in_this_step\
            and (v.val or not v.vld_mask)
        return self.BIT_t.from_py(int(is_rising), int(bool(v.vld_mask)))

    def _onFallingEdge(self):
        v = self.val
        is_falling = self in self.sim._updated_in_this_step\
            and (not v.val or not v.vld_mask)
        return self.BIT_t.from_py(int(is_falling), int(bool(v.vld_mask)))

    def __getitem__(self, index):
        if not isinstance(self._dtype, Array3t):
            raise TypeError("%r is not iterable because it uses type %r"
                            % (self, self._dtype))
        elif index < 0 or index >= self._dtype.size:
            raise IndexError(self._dtype.size, index)
        else:
            return BasicRtlSimProxyArrItem(self, index)

    def __len__(self):
        if not isinstance(self._dtype, Array3t):
            raise TypeError("%r is not iterable because it uses type %r"
                            % (self, self._dtype))
        else:
            return self._dtype.size

    def __repr__(self):
        return "<%s %r.%s %r %r>" % (self.__class__.__name__, self.parent,
                                     self.name, self.val, self.val_next)


class BasicRtlSimProxyArrItem():
    """
    Virtual proxy for an array item of BasicRtlSimProxy
    """

    def __init__(self, parent_proxy, item_index):
        self.parent_proxy = parent_proxy
        self.item_index = item_index
        self.sim = parent_proxy.sim
        self.parent = parent_proxy.parent
        self._dtype = parent_proxy._dtype.element_t

    def read(self):
        assert self.sim.read_only_not_write_only
        v = self.parent_proxy.val.val.get(self.item_index, None)
        if v is None:
            return self._dtype.from_py(None)

        return v.__copy__()
