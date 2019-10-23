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

PyObject * PySim_set_write_only(_PySim_t<void*> * self, PyObject* args) {
	self->read_only_not_write_only = false;
	Py_RETURN_NONE;
}

PyMemberDef PySim_members[8] = {
	{(char *)"io", T_OBJECT, offsetof(_PySim_t<void>, io), 0,
			(char *)"container of signals in simulation"},
	{(char *)"time", T_ULONGLONG, offsetof(_PySim_t<void>, time), 0,
    	(char *)"actual simulation time"},
    {(char *)"read_only_not_write_only", T_BOOL, offsetof(_PySim_t<void>, read_only_not_write_only), 0,
    	(char *)"if true the IO can be only read if false the IO can be only written"},

	{(char *)"COMB_UPDATE_DONE", T_INT, offsetof(_PySim_t<void>, COMB_UPDATE_DONE), 0,
			(char *)"all non edge dependent updates done"},
	{(char *)"BEFORE_EDGE", T_INT, offsetof(_PySim_t<void>, BEFORE_EDGE), 0,
			(char *)"before evaluation of edge dependent event"},
    {(char *)"END_OF_STEP", T_INT, offsetof(_PySim_t<void>, END_OF_STEP), 0,
    		(char *)"all parts of circuit updated and stable"},

	{(char *)"pending_event_list", T_OBJECT, offsetof(_PySim_t<void>, pending_event_list), 0,
    		(char *)"List of triggered callbacks"},
    {nullptr}
};
