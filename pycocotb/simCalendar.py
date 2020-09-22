from sortedcontainers.sorteddict import SortedDict
from typing import Tuple


class DONE:
    pass


class SimTimeSlot():
    """
    :note: write/read only is related
           to access to circuit from python code
    :note: event types
        * timeslot_begin
        * write_only     - w
        * "circuit eval() memory update detected"
        * comb_read      - r
        * comb_stable    - r
        * mem_stable     - r ("rest of circuit eval()")
        * timeslot_end   - r
    :note: if write_only is required in comb_stable or later error is rised
        if it called before the SimTimeSlot is evaluated from beginning
    """
    __slots__ = ['timeslot_begin', 'write_only', 'comb_read', 'comb_stable', 'mem_stable', 'timeslot_end']

    def __init__(self):
        self.timeslot_begin = None
        self.write_only = None
        self.comb_read = None
        self.comb_stable = None
        self.mem_stable = None
        self.timeslot_end = None

    def get_state_name(self):
        if self.timeslot_begin is not DONE:
            return "timeslot_begin"
        elif self.write_only is not DONE:
            return "write_only"
        elif self.comb_read is not DONE:
            return "comb_read"
        elif self.mem_stable is not DONE:
            return "mem_stable"
        elif self.timeslot_end is not DONE:
            return "timeslot_end"
        else:
            return "after timeslot_end"

    def __repr__(self):
        return "<%s in %s>" % (self.__class__.__name__, self.get_state_name())


# internal
class SimCalendar(SortedDict):
    """
    Priority queue where key is time and priority
    """

    def push(self, time: int, value: SimTimeSlot):
        assert isinstance(time, int)
        super(SimCalendar, self).__setitem__(time, value)

    def pop(self) -> Tuple[int, object]:
        return super(SimCalendar, self).popitem(0)
