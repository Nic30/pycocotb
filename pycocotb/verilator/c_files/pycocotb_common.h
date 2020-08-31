#pragma once

#include <vector>
#include <unordered_set>
#include <functional>
#include <iostream>

#include <boost/coroutine2/all.hpp>

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <structmember.h>

#include <verilated.h>
#include <verilated_vcd_c.h>

enum SimEventType {
	SIM_EV_COMB_UPDATE_DONE, // all non edge dependent updates done
	// there is last time to restart the simulation steps for combinational loops
	SIM_EV_BEFORE_EDGE, // before evaluation of edge dependent event
	SIM_EV_END_OF_STEP, // all parts of circuit updated and stable
};

// Coroutine which generates pairs <isEndOfSim, clockSignal*>
using sim_step_t = boost::coroutines2::coroutine<std::pair<SimEventType, CData*>>;

// raised if current delata step should be restarted instead of finishing of the evaluation
class DeltaStepRestart: public std::exception {
	using std::exception::exception;
};
