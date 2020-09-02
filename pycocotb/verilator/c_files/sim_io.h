#pragma once

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include "signal_mem_proxy.h"
#include "signal_array_mem_proxy.h"

struct PySimIo_t {
	PyObject_HEAD
	PyObject* dict;
};

extern PyTypeObject PySimIo_pytype;

struct SignalProxyPtr_t {
	SignalMemProxy_t * scalar;
	SignalArrayMemProxy_t * vector;
	SignalProxyPtr_t(SignalMemProxy_t * _scalar) :
			scalar(_scalar), vector(nullptr) {
	}
	SignalProxyPtr_t(SignalArrayMemProxy_t * _vector) :
			scalar(nullptr), vector(_vector) {
	}

	void destroy() {
		if (scalar) {
			scalar->signal = nullptr;
			Py_DECREF(scalar);
		}
		if (vector) {
			vector->signal = nullptr;
			Py_DECREF(vector);
		}
	}

};

// Initialize PySimIo_pytype and it's dependencies
int PySimIo_pytype_prepare();

int PySim_add_proxy(std::vector<const char *> signal_name, uint8_t * sig_addr,
		std::vector<size_t> type_width, bool is_signed,
		const bool * read_only_not_write_only, PyObject * io,
		std::vector<SignalProxyPtr_t> & signals,
		std::unordered_set<SignalMemProxy_t*> & event_triggering_signals);

int PySim_add_scalar_proxy(const char * signal_name, uint8_t * sig_addr,
		size_t type_width, bool is_signed,
		const bool * read_only_not_write_only, PyObject * io,
		std::vector<SignalProxyPtr_t> & signals,
		std::unordered_set<SignalMemProxy_t*> & event_triggering_signals);

int PySim_add_arr_proxy(const char * signal_name, uint8_t * sig_addr,
		std::vector<size_t> type_width, bool is_signed,
		const bool * read_only_not_write_only, PyObject * io,
		std::vector<SignalProxyPtr_t> & signals);

// https://gist.github.com/maddouri/0da889b331d910f35e05ba3b7b9d869b
/// This template is used to optionally call PySim_add_proxy if the signal was not optimised out
/// by Verilator
#define define_proxy_constructor(member_name)                                             \
/* struct which check if the T has property member_name */                                \
template <typename T>                                                                     \
struct dut_has_##member_name {                                                            \
    typedef char yes_type;                                                                \
    typedef long no_type;                                                                 \
    template <typename U> static yes_type test(decltype(&U::member_name));                \
    template <typename U> static no_type test(...);                                       \
    static constexpr bool Has = sizeof(test<T>(0)) == sizeof(yes_type);                   \
};                                                                                        \
/* function which is used if the T has member_name property */                            \
template<typename DUT_t>                                                                  \
int construct_proxy_##member_name(std::vector<const char *> signal_name, DUT_t * dut,     \
		std::vector<size_t> type_width, bool is_signed,                                   \
		const bool * read_only_not_write_only, PyObject * io,                             \
		std::vector<SignalProxyPtr_t> & signals,                                          \
		std::unordered_set<SignalMemProxy_t*> & event_triggering_signals,                 \
		std::true_type) {                                                                 \
	uint8_t * sig_addr = reinterpret_cast<uint8_t*>(&dut->member_name);                   \
	return PySim_add_proxy(signal_name, sig_addr, type_width, is_signed,                  \
			read_only_not_write_only, io, signals,                                        \
			event_triggering_signals);                                                    \
}                                                                                         \
/* function which is dummy call if the T has not property member_name */                  \
template<typename DUT_t>                                                                  \
int construct_proxy_##member_name(std::vector<const char *> signal_name, DUT_t * dut,     \
		std::vector<size_t> type_width, bool is_signed,                                   \
		const bool * read_only_not_write_only, PyObject * io,                             \
		std::vector<SignalProxyPtr_t> & signals,                                          \
		std::unordered_set<SignalMemProxy_t*> & event_triggering_signals,                 \
		std::false_type) {                                                                \
	return 0;                                                                             \
}                                                                                         \
/* wrapper which selects between real and dummy constructor call */                       \
template<typename DUT_t>                                                                  \
int construct_proxy_##member_name(std::vector<const char *> signal_name, DUT_t * dut,     \
		std::vector<size_t> type_width, bool is_signed,                                   \
		const bool * read_only_not_write_only, PyObject * io,                             \
		std::vector<SignalProxyPtr_t> & signals,                                          \
		std::unordered_set<SignalMemProxy_t*> & event_triggering_signals) {               \
	auto constexpr has = dut_has_##member_name<DUT_t>::Has;                               \
	                                                                                      \
   return construct_proxy_##member_name<DUT_t>(signal_name, dut,                          \
    		type_width, is_signed,                                                        \
			read_only_not_write_only, io, signals,                                        \
			event_triggering_signals,                                                     \
			std::integral_constant<bool, has>());                                         \
}
