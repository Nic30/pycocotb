from pycocotb.basic_hdl_simulator.basicSimIo import BasicSimIo


class BasicRtlSimulator():
    COMB_UPDATE_DONE = 0  # all non edge dependent updates done"},
    BEFORE_EDGE = 1  # before evaluation of edge dependent event"},
    END_OF_STEP = 2  # all parts of circuit updated and stable

    def __init__(self):
        self.io = BasicSimIo()  # container of signals in simulation
        self.time = 0  # actual simulation time
        # if true the IO can be only read if false the IO can be only written
        self.read_only_not_write_only = False
        self.pending_event_list = []  # List of triggered callbacks

    def eval(self):
        "single simulation step"

    def reset_eval(self):
        "reset evaluation"

    def set_trace_file(self, file_name, trace_depth):
        """
        set file where data from signals should be stored
        :param file_name: name of file where trace should be stored (path of vcd file f.e.)
        :param trace_depth: number of hyerarchy levels which should be trraced (-1 = all)
        """

    def set_write_only(self):
        """set simulation to write only state, should be called before entering to new evaluation step"""

    def finalize(self):
        "flush output and clean all pending actions"
