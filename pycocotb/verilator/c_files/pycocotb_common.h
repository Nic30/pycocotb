#pragma once

#include <verilated.h>
#include <verilated_vcd_c.h>
#include <Python.h>
#include <structmember.h>
#include <vector>
#include <unordered_set>
//#include <iostream>
#include <boost/coroutine2/all.hpp>
#include <functional>

#include "signal_mem_proxy.h"


enum SimEventType {
	SIM_EV_COMB_UPDATE_DONE, // all non edge dependent updates done
	// there is last time to restart the simulation steps for combinational loops
	SIM_EV_BEFORE_EDGE, // before evaluation of edge dependent event
    SIM_EV_END_OF_STEP, // all parts of circuit updated and stable
};

// Coroutine which generates pairs <isEndOfSim, clockSignal*>
using sim_step_t = boost::coroutines2::coroutine<std::pair<SimEventType, CData*>>;
