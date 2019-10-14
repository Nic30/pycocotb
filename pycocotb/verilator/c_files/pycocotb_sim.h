#pragma once

#include "pycocotb_common.h"
#include "sim_io.h"

/*
 * Main Python type of the Verilator simulator
 * */
template<typename DUT_t>
struct _PySim_t {
	PyObject_HEAD
	// simulator of DUT
	DUT_t * dut;
	// coroutine of simulation step
	sim_step_t::pull_type * actual_sim_step;
	// python IO for signals
	std::vector<SignalProxyPtr_t> * signals;
	// set of singals which have sim. process which waits on event on this signal
	std::unordered_set<SignalMemProxy_t*> * event_triggering_signals;
	bool read_only_not_write_only;
	// VCD writter
	VerilatedVcdC* tfp;
	// VCD file name
	char * trace_file_name;
	// list of sim. processes which should be woken up
	PyObject * pending_event_list;
	// Current simulation time
	vluint64_t time;
	// constants
	int COMB_UPDATE_DONE;
	int BEFORE_EDGE;
	int END_OF_STEP;
	PyObject * io; // object to store signal proxies under it's names
};

// The methods witch does not depend on DUT type are precompiled to same compilation time later
int PySim_eval_event_triggers(_PySim_t<void*>* self);
PyObject * PySim_eval(_PySim_t<void*>* self, PyObject* args);
PyObject * PySim_set_write_only(_PySim_t<void*> * self, PyObject* args);

extern PyMemberDef PySim_members[8];


template<typename DUT_t>
PyObject * PySim_set_trace_file(_PySim_t<DUT_t> * self, PyObject* args) {
	char * trace_file = nullptr;
	int trace_level = 99;
	if (!PyArg_ParseTuple(args, "si", &trace_file, &trace_level))
		return nullptr;

	if (self->tfp != nullptr
			&& strcmp(self->trace_file_name, trace_file) != 0) {
		// different trace file will be used now
		self->tfp->close();
		Verilated::traceEverOn(true);
		delete self->tfp;
		self->tfp = nullptr;
		free(self->trace_file_name);
	} else if (self->tfp == nullptr) {
		Verilated::traceEverOn(true);
		self->trace_file_name = strdup(trace_file);
		Verilated::traceEverOn(true);  // Verilator must compute traced signals
		self->tfp = new VerilatedVcdC;
		self->dut->trace(self->tfp, trace_level); // Trace x levels of hierarchy
		self->tfp->open(self->trace_file_name);  // Open the dump file
		self->tfp->dump(0);
	}

	Py_RETURN_NONE;
}

template<typename DUT_t>
PyObject * PySim_finalize(_PySim_t<DUT_t>* self, PyObject* args) {
	// Cancel all pending python callbacks to prevent mem leaks
	for (auto & s : *self->signals) {
		auto scl = s.scalar;
		if (!scl)
			continue;
		auto cbs = scl->callbacks;
		auto len = PySequence_Length(cbs);
		if (len > 0) {
			if (PySequence_DelSlice(cbs, 0, len) < 0) {
				return nullptr;
			}
		}
	}
	delete self->actual_sim_step;
	self->actual_sim_step = nullptr;
	self->dut->final();

	if (self->tfp) {
		self->tfp->flush();
		self->tfp->close();
		delete self->tfp;
		self->tfp = nullptr;
		free(self->trace_file_name);
		self->trace_file_name = nullptr;
	}
	Py_RETURN_NONE;
}

template<typename DUT_t>
void PySim_dealloc(_PySim_t<DUT_t>* self) {
	auto res = PySim_finalize(self, nullptr);
	Py_DECREF(res);

	delete self->event_triggering_signals;

	for (auto & s : *self->signals) {
		s.destroy();
	}
	delete self->signals;
	delete self->dut;

	Py_TYPE(self)->tp_free((PyObject*) self);
}

template<typename DUT_t>
static void PySim_call_eval_sim(sim_step_t::push_type &sink, DUT_t * sim) {
	sim->__pause_sink = &sink;
	for (;;) {
		sim->eval();
	}
}

template<typename DUT_t>
PyObject * PySim_eval(_PySim_t<DUT_t>* self, PyObject* args) {
	if (self->actual_sim_step) {
		(*(self->actual_sim_step))();
	} else {
		using std::placeholders::_1;
		// _1 means first parameter of call_eval will be sim
		// when coroutine obj. is constructed function is evaluated
		// until sink is triggered
		self->actual_sim_step = new sim_step_t::pull_type(
				std::bind(PySim_call_eval_sim<DUT_t>, _1, self->dut));
	}
	self->read_only_not_write_only = true;

	if (PySim_eval_event_triggers(reinterpret_cast<_PySim_t<void*>*>(self)) < 0)
		return nullptr;
	auto end_type = self->actual_sim_step->get().first;
	// Dump trace data for this step
	// end_type == SIM_EV_END_OF_STEP &&
	if (self->tfp) {
		// auto vlSymsp = self->dut->__VlSymsp;  // Setup global symbol table
		// printf("dump-end-of-step %lu __Vm_activity: %u __Vm_didInit: %u \n",
		// 		self->time, vlSymsp->__Vm_activity, vlSymsp->__Vm_didInit);
		self->tfp->dump(self->time);
	}
	return PyLong_FromLong(end_type);
}

template<typename DUT_t>
PyObject * PySim_reset_eval(_PySim_t<DUT_t>* self, PyObject* args) {
	self->dut->__restart_delta_step = true;
	self->read_only_not_write_only = false;
	if (self->tfp) {
		// printf("PySim_reset_eval %lu\n", self->time);
		self->tfp->dump(self->time);
	}
	Py_RETURN_NONE;
}
