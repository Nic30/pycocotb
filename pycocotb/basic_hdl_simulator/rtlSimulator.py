from enum import Enum
from typing import Tuple, Callable, Generator, Optional

from pycocotb.basic_hdl_simulator.io import BasicRtlSimIo
from pycocotb.basic_hdl_simulator.model import BasicRtlSimModel
from pycocotb.basic_hdl_simulator.proxy import BasicRtlSimProxy
from pycocotb.basic_hdl_simulator.sim_utils import ValueUpdater,\
    ArrayValueUpdater


class BasicRtlSimulatorSt(Enum):
    PRE_SET = 0
    EVAL_COMB = 1  # eval circuit without update of memory elements
    EVAL_SEQ = 2  # update whole circuit


def isEvDependentOn(sig: BasicRtlSimProxy, process) -> bool:
    """
    Check if hdl process has event dependency on signal
    """
    if sig is None:
        return False

    return process in sig.simFallingSensProcs\
        or process in sig.simRisingSensProcs


class BasicRtlSimulator():
    COMB_UPDATE_DONE = 0  # all non edge dependent updates done"},
    BEFORE_EDGE = 1  # before evaluation of edge dependent event"},
    END_OF_STEP = 2  # all parts of circuit updated and stable

    def __init__(self):
        self._init_main()
        self._init_listeners()

    def _init_main(self):
        # container of signals in simulation
        self.io = None  # type: BasicRtlSimIo
        self.model = None  # type: BasicRtlSimModel
        self.time = 0  # actual simulation time
        # if true the IO can be only read if false the IO can be only written
        self.read_only_not_write_only = False
        self.pending_event_list = []  # List of triggered callbacks
        self.state = BasicRtlSimulatorSt.PRE_SET
        self._proc_outputs = {}
        self._updates_to_apply = []
        self.signals_checked_for_change = set()
        self._comb_procs_to_run = set()
        self._seq_procs_to_run = set()
        self._updated_in_this_step = set()
        self.needs_init = True

    def _init_listeners(self):
        self.logChange = False
        self.logPropagation = False
        self.logApplyingValues = False

    def bound_model(self, model: BasicRtlSimModel):
        self.model = model
        self.io = model.io
        self._bound_model_procs(model)

    def _bound_model_procs(self, m: BasicRtlSimModel):
        for p, outputs in m._outputs.items():
            assert p not in self._proc_outputs
            self._proc_outputs[p] = tuple(outputs)
        for u in m._units:
            self._bound_model_procs(u)

    def _init_model_signals(self, model: BasicRtlSimModel) -> None:
        """
        * Inject default values to simulation
        * Instantiate IOs for every process
        """
        # set initial value to all signals and propagate it
        for s in model._interfaces:
            if s.def_val is not None:
                s._apply_update(ValueUpdater(s.def_val, False))

        for u in model._units:
            self._init_model_signals(u)

        for p in model._processes:
            self._add_hdl_proc_to_run(None, p)

    def _add_hdl_proc_to_run(self, trigger: Optional[BasicRtlSimProxy], proc) -> None:
        """
        Add hdl process to execution queue
        :param trigger: instance of SimSignal
        :param proc: python generator function representing HDL process
        """
        # first process in time has to plan executing of apply values on the
        # end of this time
        if isEvDependentOn(trigger, proc):
            if self.time == 0:
                return  # pass event dependent on startup
            self._seq_procs_to_run.add(proc)
        else:
            self._comb_procs_to_run.add(proc)

    def _mkUpdater(self, newValue)\
            -> Tuple[Callable[["Value"], bool], bool]:
        """
        This functions resolves write conflicts for signal
        """
        invalidate = False
        if len(newValue) == 3:
            # update for item in array
            val, indexes, isEvDependent = newValue
            return (ArrayValueUpdater(val, indexes, invalidate), isEvDependent)
        else:
            # update for simple signal
            val, isEvDependent = newValue
            return (ValueUpdater(val, invalidate), isEvDependent)

    def _run_comb_processes(self) -> None:
        """
        Delta step for combinational processes
        """
        while self._comb_procs_to_run:
            for proc in self._comb_procs_to_run:
                io = self._proc_outputs[proc]
                proc()
                for sig in io:
                    if sig.val_next is not None:
                        res = self._mkUpdater(sig.val_next)
                        # prepare update
                        updater, is_event_dependent = res
                        self._updates_to_apply.append(
                            (sig, updater, is_event_dependent, proc)
                        )
                        sig.val_next = None
                        # else value is latched
            self._comb_procs_to_run.clear()

            va = self._updates_to_apply
            # log if there are items to log
            lav = self.logApplyingValues
            if va and lav:
                lav(self, va)
            self._updates_to_apply = []

            # apply values to signals, values can overwrite each other
            # but each signal should be driven by only one process and
            # it should resolve value collision
            addSp = self._seq_procs_to_run.add
            for s, vUpdater, isEventDependent, comesFrom in va:
                if isEventDependent:
                    # now=0 and this was process initialization or async reg
                    addSp(comesFrom)
                else:
                    # regular combinational process
                    s._apply_update(vUpdater)

    def _run_seq_processes(self) -> Generator[None, None, None]:
        """
        Delta step for event dependent processes
        """
        updated = []
        for proc in self._seq_procs_to_run:
            io = self._proc_outputs[proc]
            proc()
            updated.extend(io)

        self._seq_procs_to_run = set()

        for sig in updated:
            if sig.val_next is not None:
                v = self._mkUpdater(sig.val_next)
                updater, _ = v
                sig._apply_update(updater)
                sig.val_next = None

    def eval(self):
        "single simulation step"
        if self.needs_init:
            self._init_model_signals(self.model)
            self.needs_init = False

        st = self.state
        if st == BasicRtlSimulatorSt.PRE_SET:
            # apply all writes from outside world
            self.state = BasicRtlSimulatorSt.EVAL_COMB
            self.read_only_not_write_only = True
            self._run_comb_processes()
            return self.COMB_UPDATE_DONE
        elif st == BasicRtlSimulatorSt.EVAL_COMB:
            # evaluate all combinational paths
            # without updating any memory element
            self.state = BasicRtlSimulatorSt.EVAL_SEQ
            self._run_comb_processes()
            return self.BEFORE_EDGE
        elif st == BasicRtlSimulatorSt.EVAL_SEQ:
            # update rest of the circuit including memories
            self._run_comb_processes()
            self._run_seq_processes()
            self._run_comb_processes()
            self.state = BasicRtlSimulatorSt.PRE_SET
            self._updated_in_this_step.clear()
            return self.END_OF_STEP
        else:
            raise AssertionError("Invalid state", self.state)

    def reset_eval(self):
        """
        reset evaluation in COMB_UPDATE_DONE state
        so the comb. circuits can be evaluated again
        """
        assert self.state == BasicRtlSimulatorSt.EVAL_COMB, (self.state, self.time)
        self.state = BasicRtlSimulatorSt.PRE_SET
        self.read_only_not_write_only = False

    def set_trace_file(self, file_name, trace_depth):
        """
        set file where data from signals should be stored

        :param file_name: name of file where trace should be stored (path of vcd file f.e.)
        :param trace_depth: number of hyerarchy levels which should be trraced (-1 = all)
        """
        raise NotImplementedError()

    def set_write_only(self):
        """
        set simulation to write only state, should be called
        before entering to new evaluation step"""
        self.read_only_not_write_only = False
        assert self.state == BasicRtlSimulatorSt.PRE_SET, self.state

    def finalize(self):
        "flush output and clean all pending actions"
