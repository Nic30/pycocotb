#pragma once

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <vector>
#include <unordered_set>

/*
 * Proxy for memory of signal in simulation. Allows r/w access from python and value change detection.
 * */
struct SignalMemProxy_t {
    PyObject_HEAD
	bool is_read_only; // flag which tells if this signal can be written
	uint8_t * signal; // pointer to memory where signal value is stored in simulator
	size_t signal_bits; // size of value in bits
	size_t signal_bytes; // size of value in bytes (cached to simplify math)
	uint8_t last_byte_mask; // validity mask for last byte
	bool is_signed; // flag for value of signed type
	// flag to specify allowed IO operations
	const bool * read_only_not_write_only;
	// python functions which are called when value of this signal changes
	PyObject * callbacks;
	// set of signals which are checked for change after each step
	// because there is a process which waits for event on this signal
	std::unordered_set<SignalMemProxy_t*> * signals_checked_for_change;
	uint8_t * value_cache; // buffer to store previous value for event detection

	// properties used for simplified associations and debug in python
	PyObject * name; // physical name
	PyObject * _name; // logical name
	PyObject * _dtype; // type notation for python
	PyObject * _origin; // signal object which this proxy substitutes
	PyObject * _ag; // simulation agent which drive or monitor this signal
};

/*
 * Initialise SignalMemProxy_t
 * */
void SignalMemProxy_c_init(SignalMemProxy_t * self, bool is_read_only,
		uint8_t * signal, size_t signal_bits, bool is_signed, const char * name,
		std::unordered_set<SignalMemProxy_t*> * signals_checked_for_change,
		const bool * read_only_not_write_only);

/*
 * Store actual value for later change detection
 * */
void SignalMemProxy_cache_value(SignalMemProxy_t* self);

/*
 * Evaluate if value changed
 * @note SignalMemProxy_cache_value has to be called first
 * */
bool SignalMemProxy_value_changed(SignalMemProxy_t* self);

extern PyTypeObject SignalMemProxy_pytype;

