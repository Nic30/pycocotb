#pragma once

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
 * Initialize SignalMemProxy_t
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

// https://gist.github.com/maddouri/0da889b331d910f35e05ba3b7b9d869b
/// This template is used to optionally call PySim_add_proxy if the signal was not optimised out
/// by Verilator
#define define_proxy_constructor(member_name)                                             \
template <typename T>                                                                     \
struct dut_has_##member_name {                                                            \
    typedef char yes_type;                                                                \
    typedef long no_type;                                                                 \
    template <typename U> static yes_type test(decltype(&U::member_name));                \
    template <typename U> static no_type test(...);                                       \
    static constexpr bool Has = sizeof(test<T>(0)) == sizeof(yes_type);                   \
};                                                                                        \
                                                                                          \
template<typename DUT_t>                                                                  \
int construct_proxy_##member_name(std::vector<const char *> signal_name, DUT_t * dut,     \
		std::vector<size_t> type_width, bool is_signed,                                   \
		const bool * read_only_not_write_only, PyObject * io,                             \
		std::vector<SignalMemProxy_t*> & signals,                                         \
		std::unordered_set<SignalMemProxy_t*> & event_triggering_signals,                 \
		std::true_type) {                                                                 \
	uint8_t * sig_addr = reinterpret_cast<uint8_t*>(&dut->member_name);                   \
	return PySim_add_proxy(signal_name, sig_addr, type_width, is_signed,                  \
			read_only_not_write_only, io, signals,                                        \
			event_triggering_signals);                                                    \
}                                                                                         \
                                                                                          \
template<typename DUT_t>                                                                  \
int construct_proxy_##member_name(std::vector<const char *> signal_name, DUT_t * dut,     \
		std::vector<size_t> type_width, bool is_signed,                                   \
		const bool * read_only_not_write_only, PyObject * io,                             \
		std::vector<SignalMemProxy_t*> & signals,                                         \
		std::unordered_set<SignalMemProxy_t*> & event_triggering_signals,                 \
		std::false_type) {                                                                \
	return 0;                                                                             \
}                                                                                         \
                                                                                          \
template<typename DUT_t>                                                                  \
int construct_proxy_##member_name(std::vector<const char *> signal_name, DUT_t * dut,     \
		std::vector<size_t> type_width, bool is_signed,                                   \
		const bool * read_only_not_write_only, PyObject * io,                             \
		std::vector<SignalMemProxy_t*> & signals,                                         \
		std::unordered_set<SignalMemProxy_t*> & event_triggering_signals) {               \
	auto constexpr has = dut_has_##member_name<DUT_t>::Has;                               \
	                                                                                      \
    return construct_proxy_##member_name<DUT_t>(signal_name, dut, type_width, is_signed,  \
			read_only_not_write_only, io, signals,                                        \
			event_triggering_signals,                                                     \
			std::integral_constant<bool, has>());                                         \
}                                                                                         \

