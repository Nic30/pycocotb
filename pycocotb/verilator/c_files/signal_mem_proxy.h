#pragma once

#include <Python.h>

typedef struct {
    PyObject_HEAD
	bool is_read_only;
	uint8_t * signal;
	size_t signal_size;
	bool is_signed;

	// properties used for simplified associations and debug in python
	PyObject * name; // physical name
	PyObject * _name; // logical name
	PyObject * _dtype; // type notation for python
	PyObject * _origin; // signal object which this proxy substitutes
	PyObject * _ag; // simulation agent which drive or monitor this signal
} SignalMemProxy_t;


void SignalMemProxy_c_init(SignalMemProxy_t * self, bool is_read_only,
		uint8_t * signal, size_t signal_size, bool is_signed, const char * name);

extern PyTypeObject SignalMemProxy_pytype;
