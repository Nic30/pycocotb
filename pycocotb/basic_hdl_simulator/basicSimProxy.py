

class BasicSimProxy():
    """
    Signal proxy which manages the access to a memory in simulation
    """
    __slots__ = ["callbacks", "sim", "name", "_name",
                 "_dtype", "_origin", "_ag"]

    def __init__(self, sim: "BasicRtlSimulator", io, io_prev, name, dtype):
        self.callbacks = []
        self.sim = sim
        self.io = io
        self.io_prev = io_prev
        # properties used for simplified associations and debug in python
        self.name = name  # physical name
        self._name = name  # logical name
        self._dtype = dtype  # type notation for python
        self._origin = None  # signal object which this proxy substitutes
        self._ag = None  # simulation agent which drive or monitor this signal

    def read(self):
        assert self.sim.read_only_not_write_only
        return getattr(self.io, self._name)

    def write(self, val):
        assert not self.sim.read_only_not_write_only
        val = self._dtype.from_py(val)
        setattr(self.io, self._name, val)

    def wait(self, cb):
        self.callbacks.append(cb)
        self.sim.signals_checked_for_change.add(cb)
