#include "signal_array_mem_proxy.h"
#include "signal_mem_proxy.h"
#include <structmember.h>

size_t ceil_div(size_t a, size_t b) {
	size_t res = a / b;
	if (res * b < a)
		res += 1;
	return res;
}

/*
 * @return number of bytes for the representation of the item
 * */
size_t get_real_size_of_verilator_array_item(size_t bit_lenght_of_item) {
	// uint8_t name    ///< Declare signal, 1-8 bits
	// uint16_t name   ///< Declare signal, 9-16 bits
	// uint64_t name   ///< Declare signal, 33-64 bits
	// IData name		///< Declare signal, 17-32 bits
	// uint32_t name[words]	///< Declare signal, 65+ bits
	if (bit_lenght_of_item <= 8)
		return 1;
	else if (bit_lenght_of_item <= 16)
		return 2;
	else if (bit_lenght_of_item <= 32)
		return 4;
	else if (bit_lenght_of_item <= 64)
		return 8;
	else {
		return 4 * ceil_div(bit_lenght_of_item, 32);
	}
}

/*
 * @note first element of dim is interpreted as a number of elements in this array
 * */
size_t get_real_size_of_verilator_array_item(std::vector<size_t> dim) {
	size_t size = 1;
	size_t last = dim.size() - 1;
	for (size_t i = 0; i < dim.size(); i++) {
		if (i == last) {
			size *= get_real_size_of_verilator_array_item(dim[i]);
		} else {
			size *= dim[i];
		}
	}
	return size;
}

void SignalArrayMemProxy_c_init(SignalArrayMemProxy_t * self, bool is_read_only,
		uint8_t * signal, std::vector<size_t> dim, bool is_signed,
		const char * name, const bool * read_only_not_write_only) {
	self->is_read_only = is_read_only;
	self->signal = signal;
	assert(dim.size() > 1);
	self->dim = new std::vector<size_t>(dim);
	self->element_cnt = dim[0];
	self->element_bytes = get_real_size_of_verilator_array_item(dim);
	self->is_signed = is_signed;
	if (name)
		self->name = PyUnicode_FromString(name);
	self->read_only_not_write_only = read_only_not_write_only;
}

static void SignalArrayMemProxy_dealloc(SignalArrayMemProxy_t* self) {
	Py_XDECREF(self->name);
	Py_XDECREF(self->_name);
	Py_XDECREF(self->_origin);
	Py_XDECREF(self->_dtype);

	delete self->dim;

	Py_TYPE(self)->tp_free((PyObject*) self);
}
static PyObject *
SignalArrayMemProxy_new(PyTypeObject *type, PyObject *args, PyObject *kwds) {
	SignalArrayMemProxy_t *self = (SignalArrayMemProxy_t *) type->tp_alloc(type, 0);
	if (self == nullptr) {
		PyErr_SetString(PyExc_MemoryError,
				"Can not create new instance of SignalArrayMemProxy");
		return nullptr;
	}
	self->is_read_only = true;
	self->signal = nullptr;
	self->is_signed = false;
	self->name = nullptr;
	self->read_only_not_write_only = nullptr;
	self->dim = nullptr;
	self->element_bytes = 0;
	self->element_cnt = 0;
	return (PyObject *) self;
}

static PyMemberDef SignalArrayMemProxy_members[] =
		{ { (char *) "name", T_OBJECT, offsetof(SignalArrayMemProxy_t, name), 0,          //
			(char *) "name of signal in simulation" },                               //
		  { (char *) "_name", T_OBJECT, offsetof(SignalArrayMemProxy_t, _name), 0,        //
			(char *) "logical name of signal in simulation" },                       //
		  { (char *) "_dtype", T_OBJECT, offsetof(SignalArrayMemProxy_t, _dtype),         //
			0, (char *) "type of signal in simulation" },                            //
		  { (char *) "_origin", T_OBJECT, offsetof(SignalArrayMemProxy_t, _origin), 0,    //
			(char *) "original signal object for this signal proxy in simulation" }, //
		  { (char *) "_ag", T_OBJECT, offsetof(SignalArrayMemProxy_t, _origin), 0,        //
		    (char *) "simulation agent which drive or monitor this signal" },        //
		  { nullptr } /* Sentinel */
		};

Py_ssize_t SignalArrayMemProxy_sq_length(SignalArrayMemProxy_t * self) {
	return self->element_cnt;
}

PyObject * SignalArrayMemProxy_sq_item(SignalArrayMemProxy_t * self,
		Py_ssize_t i) {
	if (i >= (Py_ssize_t)self->element_cnt || i < 0) {
		PyErr_SetString(PyExc_IndexError,
				"SignalArrayMemProxy index out of range");
		return nullptr;
	}
	uint8_t * sig_addr = self->signal + self->element_bytes * i;
	size_t dims = self->dim->size();
	if (dims == 2) {
		// item is scalar
		SignalMemProxy_t * proxy = (SignalMemProxy_t *) PyObject_CallObject(
				(PyObject*) &SignalMemProxy_pytype, nullptr);
		if (!proxy) {
			PyErr_SetString(PyExc_AssertionError,
					"Can not create signal proxy for array item");
			return nullptr;
		}
		SignalMemProxy_c_init(proxy, true, sig_addr, (*self->dim)[1],
				self->is_signed, nullptr, nullptr,
				self->read_only_not_write_only);
		return (PyObject* )proxy;
	} else if (dims > 2) {
		std::vector<size_t> type_width(dims - 1);
		std::copy(self->dim->begin() + 1, self->dim->end(), type_width.begin());
		// item is a array
		SignalArrayMemProxy_t * proxy =
				(SignalArrayMemProxy_t *) PyObject_CallObject(
						(PyObject*) &SignalArrayMemProxy_pytype, nullptr);
		if (!proxy) {
			PyErr_SetString(PyExc_AssertionError,
					"Can not create signal proxy");
			return nullptr;
		}
		SignalArrayMemProxy_c_init(proxy, true, sig_addr, type_width,
				self->is_signed, nullptr, self->read_only_not_write_only);
		return (PyObject* )proxy;
	} else {
		PyErr_SetString(PyExc_AssertionError,
				"SignalArrayMemProxy constructed for scalar type");
		return nullptr;
	}
}

PyObject* SignalArrayMemProxy_iter(SignalArrayMemProxy_t *self) {
	SignalArrayMemProxyIterator_t * it =
			(SignalArrayMemProxyIterator_t *) PyObject_CallObject(
					(PyObject*) &SignalArrayMemProxyIterator_pytype, nullptr);
	if (it == nullptr)
		return nullptr;
	it->proxy = self;
	it->actual_index = 0;

	return (PyObject* )it;
}

static PySequenceMethods SignalArrayMemProxy_tp_as_sequence = {
	   (lenfunc)SignalArrayMemProxy_sq_length,//lenfunc sq_length;
	   0,//binaryfunc sq_concat;
	   0,//ssizeargfunc sq_repeat;
	   (ssizeargfunc)SignalArrayMemProxy_sq_item,//ssizeargfunc sq_item;
	   // [note] there is more of items in this stuct
};

PyTypeObject SignalArrayMemProxy_pytype = {
	PyVarObject_HEAD_INIT(nullptr, 0)
	"SignalArrayMemProxy", /* tp_name */
	sizeof(SignalArrayMemProxy_t), /* tp_basicsize */
	0, /* tp_itemsize */
	(destructor)SignalArrayMemProxy_dealloc, /* tp_dealloc */
	0, /* tp_print */
	0, /* tp_getattr */
	0, /* tp_setattr */
	0, /* tp_reserved */
	0, /* tp_repr */
	0, /* tp_as_number */
	&SignalArrayMemProxy_tp_as_sequence, /* tp_as_sequence */
	0, /* tp_as_mapping */
	0, /* tp_hash  */
	0, /* tp_call */
	0, /* tp_str */
	0, /* tp_getattro */
	0, /* tp_setattro */
	0, /* tp_as_buffer */
	Py_TPFLAGS_DEFAULT |
	Py_TPFLAGS_BASETYPE, /* tp_flags */
	"Simulation proxy for signal of array type in HDL simulation\n(set/get for memory in simulator where value of signal is stored)",/* tp_doc */
	0, /* tp_traverse */
	0, /* tp_clear */
	0, /* tp_richcompare */
	0, /* tp_weaklistoffset */
	(getiterfunc)&SignalArrayMemProxy_iter, /* tp_iter */
	0, /* tp_iternext */
	0, /* tp_methods */
	SignalArrayMemProxy_members, /* tp_members */
	0, /* tp_getset */
	0, /* tp_base */
	0, /* tp_dict */
	0, /* tp_descr_get */
	0, /* tp_descr_set */
	0, /* tp_dictoffset */
	0, /* tp_init */
	0, /* tp_alloc */
	(newfunc)SignalArrayMemProxy_new,/* tp_new */
};

PyTypeObject SignalArrayMemProxyIterator_pytype = {
	PyVarObject_HEAD_INIT(nullptr, 0)
	"SignalArrayMemProxyIterator", /* tp_name */
	sizeof(SignalArrayMemProxyIterator_t), /* tp_basicsize */
	// [note rest of the definion in type initialization fn]
};

PyObject* SignalArrayMemProxyIterator_next(
		SignalArrayMemProxyIterator_t *self) {
	if (self->actual_index < self->proxy->element_cnt) {
		auto tmp = SignalArrayMemProxy_sq_item(self->proxy, self->actual_index);
		self->actual_index++;
		return tmp;
	} else {
		/* Raising of standard StopIteration exception with empty value. */
		PyErr_SetNone(PyExc_StopIteration);
		return nullptr;
	}
}
int SignalArrayMemProxy_pytype_prepare() {
	if (PyType_Ready(&SignalArrayMemProxy_pytype) < 0) {
		return -1;
	}

	auto & t = SignalArrayMemProxyIterator_pytype;
	t.tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE;
	t.tp_doc =
			"Iterator for simulation proxy for signal of array type in HDL simulation\n"
			"(set/get for memory in simulator where value of signal is stored)";
	t.tp_iternext = (iternextfunc) &SignalArrayMemProxyIterator_next;
	t.tp_new = PyType_GenericNew;

	if (PyType_Ready(&SignalArrayMemProxyIterator_pytype) < 0) {
		return -1;
	}
	return 0;
}





