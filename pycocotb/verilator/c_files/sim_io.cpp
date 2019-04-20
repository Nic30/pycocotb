#include "sim_io.h"

static PyObject * PySimIo_new(PyTypeObject *type, PyObject *args,
		PyObject *kwds) {
	PySimIo_t * self = (PySimIo_t *) type->tp_alloc(type, 0);
	return (PyObject *) self;
}
PyTypeObject PySimIo_pytype = {
	PyVarObject_HEAD_INIT(nullptr, 0)
	"PySimIo", /* tp_name */
	sizeof(PySimIo_t), /* tp_basicsize */
	0, /* tp_itemsize */
	0, /* tp_dealloc */
	0, /* tp_print */
	0, /* tp_getattr */
	0, /* tp_setattr */
	0, /* tp_reserved */
	0, /* tp_repr */
	0, /* tp_as_number */
	0, /* tp_as_sequence */
	0, /* tp_as_mapping */
	0, /* tp_hash  */
	0, /* tp_call */
	0, /* tp_str */
	0, /* tp_getattro */
	0, /* tp_setattro */
	0, /* tp_as_buffer */
	Py_TPFLAGS_DEFAULT, /* tp_flags */
	"Container for signals in simulation", /* tp_doc */
	0, /* tp_traverse */
	0, /* tp_clear */
	0, /* tp_richcompare */
	0, /* tp_weaklistoffset */
	0, /* tp_iter */
	0, /* tp_iternext */
	0, /* tp_methods */
	0, /* tp_members */
	0, /* tp_getset */
	0, /* tp_base */
	0, /* tp_dict */
	0, /* tp_descr_get */
	0, /* tp_descr_set */
	0, /* tp_dictoffset */
	0, /* tp_init */
	0, /* tp_alloc */
	PySimIo_new, /* tp_new */
};

int PySim_add_proxy(std::vector<const char *> signal_name, uint8_t * sig_addr,
		std::vector<size_t> type_width, bool is_signed,
		const bool * read_only_not_write_only, PyObject * io,
		std::vector<SignalMemProxy_t*> & signals,
		std::unordered_set<SignalMemProxy_t*> & event_triggering_signals) {
	throw std::runtime_error("not implemented");
}

int PySim_add_proxy(const char * signal_name, uint8_t * sig_addr,
		std::vector<size_t> type_width, bool is_signed,
		const bool * read_only_not_write_only, PyObject * io,
		std::vector<SignalMemProxy_t*> & signals,
		std::unordered_set<SignalMemProxy_t*> & event_triggering_signals) {
	if (type_width.size() > 1) {
		throw std::runtime_error("not implemented");
	} else {
		Py_INCREF((PyObject*) &SignalMemProxy_pytype);
		SignalMemProxy_t * proxy = (SignalMemProxy_t *) PyObject_CallObject(
				(PyObject*) &SignalMemProxy_pytype, nullptr);
		if (!proxy) {
			PyErr_SetString(PyExc_AssertionError,
					"Can not create signal proxy");
			return -1;
		}
		SignalMemProxy_c_init(proxy, true, sig_addr, type_width.at(0), is_signed,
				signal_name, &event_triggering_signals,
				read_only_not_write_only);
		signals.push_back(proxy);
		if (PyObject_SetAttrString(io, signal_name,
				reinterpret_cast<PyObject*>(proxy))) {
			PyErr_SetString(PyExc_AssertionError,
					"Can not add signal proxy to io of simulator");
			return -1;
		}

		return 0;
	}
}
