# PyCOCOTB

[COCOTB](https://github.com/potentialventures/cocotb) like HDL simulation environment where simulation is driven from Python. 
Simulation is just an object instance and can be manipulated as any other object.
This allows better code reuse, integration with existing test frameworks and better test automation.


# Installation

* install c compiler (tested with GCC 7.3.0)
* download [verilator](https://www.veripool.org/projects/verilator/wiki/Installing)
* apply patches from `verilator_patches_tmp`
* install verilator
* run ```python3 setup.py install```
* If you want to just test this library without any kind of installation use ```python3 setup.py build``` to build c extensions.



# Current state
* alfa
* experimental Python <-> Verilator binding, experimental UVM like environment
* some examples in tests


# Similar software

* [midas](https://github.com/ucb-bar/midas)
* [firesim](https://github.com/firesim/firesim)
