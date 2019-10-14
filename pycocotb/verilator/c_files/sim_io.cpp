#include "sim_io.h"
#include <structmember.h>

PyTypeObject PySimIo_pytype;

PyMemberDef PySimIo_members[2] = {
	{(char *)"__dict__", T_OBJECT, offsetof(PySimIo_t, dict), 0,
			(char *)"dictionary with properties of the object"},
    {nullptr}
};

int PySimIo_pytype_prepare() {
	if (PyType_Ready(&SignalMemProxy_pytype) < 0) {
		return -1;
	}
	if (SignalArrayMemProxy_pytype_prepare() < 0)
		return -1;

	auto & t = PySimIo_pytype;
	memset(&PySimIo_pytype, 0, sizeof(PySimIo_pytype));
	PySimIo_pytype = {
		PyVarObject_HEAD_INIT(nullptr, 0)
		"PySimIo", /* tp_name */
		sizeof(PySimIo_t), /* tp_basicsize */
	};
	t.tp_flags = Py_TPFLAGS_DEFAULT;
	t.tp_doc = "Container for signals in simulation";
	t.tp_new = PyType_GenericNew;
	t.tp_getattro = PyObject_GenericGetAttr;
	t.tp_setattro = PyObject_GenericSetAttr;
	t.tp_dictoffset = offsetof(PySimIo_t, dict);
	t.tp_members = PySimIo_members;

	if (PyType_Ready(&PySimIo_pytype) < 0)
		return -1;

	return 0;
}

int PySim_add_proxy(std::vector<const char *> signal_name, uint8_t * sig_addr,
		std::vector<size_t> type_width, bool is_signed,
		const bool * read_only_not_write_only, PyObject * io,
		std::vector<SignalProxyPtr_t> & signals,
		std::unordered_set<SignalMemProxy_t*> & event_triggering_signals) {
	size_t name_i = 0;
	while (name_i != signal_name.size() - 1) {
		auto n = signal_name.at(name_i);
		if (PyObject_HasAttrString(io, n)) {
			io = PyObject_GetAttrString(io, n);
		} else {
			auto new_io = PyObject_CallObject(
					reinterpret_cast<PyObject*>(&PySimIo_pytype), nullptr);
			if (!new_io) {
				PyErr_SetString(PyExc_AssertionError,
						"Can not create simulation io");
				return -1;
			}
			if (PyObject_SetAttrString(io, n, new_io) < 0) {
				return -1;
			}
			io = new_io;
		}
		name_i++;
	}
	auto n = signal_name.back();
	if (type_width.size() == 1) {
		// proxy for the scalar value
		return PySim_add_scalar_proxy(n, sig_addr, type_width.at(0), is_signed,
				read_only_not_write_only, io, signals, event_triggering_signals);
	} else {
		// proxy for the array
		return PySim_add_arr_proxy(n, sig_addr, type_width, is_signed,
				read_only_not_write_only, io, signals);
	}
}

int PySim_add_scalar_proxy(const char * signal_name, uint8_t * sig_addr,
		size_t type_width, bool is_signed,
		const bool * read_only_not_write_only, PyObject * io,
		std::vector<SignalProxyPtr_t> & signals,
		std::unordered_set<SignalMemProxy_t*> & event_triggering_signals) {
	SignalMemProxy_t * proxy = (SignalMemProxy_t *) PyObject_CallObject(
			(PyObject*) &SignalMemProxy_pytype, nullptr);
	if (!proxy) {
		PyErr_SetString(PyExc_AssertionError, "Can not create signal proxy");
		return -1;
	}
	SignalMemProxy_c_init(proxy, true, sig_addr, type_width, is_signed,
			signal_name, &event_triggering_signals, read_only_not_write_only);
	signals.push_back(proxy);
	if (PyObject_SetAttrString(io, signal_name,
			reinterpret_cast<PyObject*>(proxy)) < 0) {
		return -1;
	}

	return 0;
}

int PySim_add_arr_proxy(const char * signal_name, uint8_t * sig_addr,
		std::vector<size_t> type_width, bool is_signed,
		const bool * read_only_not_write_only, PyObject * io,
		std::vector<SignalProxyPtr_t> & signals) {
	SignalArrayMemProxy_t * proxy =
			(SignalArrayMemProxy_t *) PyObject_CallObject(
					(PyObject*) &SignalArrayMemProxy_pytype, nullptr);
	if (!proxy) {
		PyErr_SetString(PyExc_AssertionError, "Can not create signal proxy");
		return -1;
	}
	SignalArrayMemProxy_c_init(proxy, true, sig_addr, type_width, is_signed,
			signal_name, read_only_not_write_only);
	signals.push_back(proxy);
	if (PyObject_SetAttrString(io, signal_name,
			reinterpret_cast<PyObject*>(proxy)) < 0) {
		return -1;
	}

	return 0;
}

