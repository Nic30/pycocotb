#include "pycocotb_sim.h"

int PySim_eval_event_triggers(_PySim_t<void*>* self) {
	for (auto s : *self->event_triggering_signals) {
		if (SignalMemProxy_value_changed(s)) {
			_PyList_Extend(
					reinterpret_cast<PyListObject*>(self->pending_event_list),
					s->callbacks);
			auto cbs = s->callbacks;
			auto len = PySequence_Length(cbs);
			if (len > 0) {
				if (PySequence_DelSlice(cbs, 0, len) < 0) {
					return -1;
				}
			}
			SignalMemProxy_cache_value(s);
		}
	}
	return 0;
}

PyObject * PySim_reset_eval(_PySim_t<void*>* self, PyObject* args) {
	if (self->actual_sim_step) {
		delete self->actual_sim_step;
		self->actual_sim_step = nullptr;
		self->read_only_not_write_only = false;
	}

	Py_RETURN_NONE;
}

PyObject * PySim_set_write_only(_PySim_t<void*> * self, PyObject* args) {
	self->read_only_not_write_only = false;
	Py_RETURN_NONE;
}
