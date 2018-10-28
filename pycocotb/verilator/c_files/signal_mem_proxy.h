#ifndef _SignalMemProxy_H_
#define _SignalMemProxy_H_

#include <Python.h>

typedef struct {
    PyObject_HEAD
	bool is_read_only;
	uint8_t * signal;
	size_t signal_size;
	bool is_signed;
	PyObject * name;
} SignalMemProxy_t;


void SignalMemProxy_c_init(SignalMemProxy_t * self, bool is_read_only,
		uint8_t * signal, size_t signal_size, bool is_signed, const char * name);

extern PyTypeObject SignalMemProxy_pytype;

#endif
