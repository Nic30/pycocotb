#pragma once

#include <Python.h>
#include "signal_mem_proxy.h"

struct PySimIo_t {
	PyObject_HEAD
};

extern PyTypeObject PySimIo_pytype;

int PySim_add_proxy(std::vector<const char *> signal_name, uint8_t * sig_addr, std::vector<size_t> type_width, bool is_signed,
			const bool * read_only_not_write_only, PyObject * io, std::vector<SignalMemProxy_t*> & signals,
			std::unordered_set<SignalMemProxy_t*> & event_triggering_signals);


int PySim_add_proxy(const char * signal_name, uint8_t * sig_addr, std::vector<size_t> type_width, bool is_signed,
			const bool * read_only_not_write_only, PyObject * io, std::vector<SignalMemProxy_t*> & signals,
			std::unordered_set<SignalMemProxy_t*> & event_triggering_signals);

