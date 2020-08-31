#pragma once

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <vector>


struct SignalArrayMemProxy_t {
	PyObject_HEAD
	bool is_read_only; // flag which tells if this signal can be written
	uint8_t * signal; // pointer to memory where signal value is stored in simulator
	std::vector<size_t> * dim;
	size_t element_cnt;
	size_t element_bytes;
	bool is_signed; // flag for value of signed type
	// flag to specify allowed IO operations
	const bool * read_only_not_write_only;

	// properties used for simplified associations and debug in python
	PyObject * name; // physical name
	PyObject * _name; // logical name
	PyObject * _dtype; // type notation for python
	PyObject * _origin; // signal object which this proxy substitutes
	PyObject * _ag; // simulation agent which drive or monitor this signal
};

struct SignalArrayMemProxyIterator_t {
	PyObject_HEAD
	size_t actual_index;
	SignalArrayMemProxy_t * proxy;
};

/*
 * Initialise SignalArrayMemProxy_t
 *
 * @param self the object to initialise
 * @param is_read_only if true this proxy forbids write
 * @param signal the pointer on target memory
 * @param dim the vector of the sizes the sequecne begins with the sizes of the array
 * 			and ends with number of bits per element
 * @param is_signed if true the element is interpreted as a signed value
 * @param name name of this array
 * @param read_only_write_only the flag which controls the IO access in write/read only phases
 * */
void SignalArrayMemProxy_c_init(SignalArrayMemProxy_t * self, bool is_read_only,
		uint8_t * signal, std::vector<size_t> dim, bool is_signed, const char * name,
		const bool * read_only_not_write_only);

extern PyTypeObject SignalArrayMemProxy_pytype;
extern PyTypeObject SignalArrayMemProxyIterator_pytype;

int SignalArrayMemProxy_pytype_prepare();

