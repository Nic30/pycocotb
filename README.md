# PyCOCOTB

[![Build Status](https://travis-ci.org/Nic30/pycocotb.svg?branch=master)](https://travis-ci.org/Nic30/pycocotb)
[![Coverage Status](https://coveralls.io/repos/github/Nic30/pycocotb/badge.svg?branch=master)](https://coveralls.io/github/Nic30/pycocotb?branch=master)
[![PyPI version](https://badge.fury.io/py/pycocotb.svg)](http://badge.fury.io/py/pycocotb)
[ROADMAP](https://drive.google.com/file/d/1zyegLIf7VaBRyb-ED5vgOMmHzW4SRZLp/view?usp=sharing)


This is a library which contains bindigns for RTL simulators and provides UVM like environment which simplifies feeding and checking the circuit running in RTL simulator.
Goal of this library is to remove obscurity and support code reuse. Each simulation is just python object without special properties. This allows also integration with existing test frameworks and better test automation and debugging.


# Installation

## Linux (Ubuntu 19.10)

* `sudo apt install build-essential python3 cmake flex bison git libboost-dev libboost-all-dev`
* download [verilator](https://www.veripool.org/projects/verilator/wiki/Installing)
* apply patches from `verilator_patches_tmp` ( as it is done in [.travis.yml](https://github.com/Nic30/pycocotb/blob/master/.travis.yml#L50))
* install verilator
* run `sudo python3 setup.py install --verilator` to install globally or `python3 setup.py install --user --verilator` to install to `~/.local/...`
* Or if you want to just test this library without any kind of installation use `python3 setup.py build --verilator` to build c extensions.

## Windows

Using windows is not recomended with verilator. Asi it is more easy to use docker than tweak Verilator to run on Windows as desired.

* install [Python 3](https://www.python.org/downloads/)
* install [Visual Studio](https://visualstudio.microsoft.com/thank-you-downloading-visual-studio/?sku=Community&rel=15) (C++)
* install [CMake](https://cmake.org/)
* install [boost](https://www.boost.org/doc/libs/1_69_0/more/getting_started/windows.html)
* install [Cygwin](https://cygwin.com/install.html) and save installer `setup-x86_64.exe` to cygwin root.
* use `ci_scripts/appveyor_install.sh` to install this library and it's dependencies

After installation verilator has to run under cygwin, but python and this library are not restricted.



# Current state - alfa
* experimental UVM like environment
* experimental Python <-> Verilator RTL simulator binding (pycocotb.verilator)
* experimental Python based RTL simulator (pycocotb.basic_hdl_simulator)
* some examples in tests
* used in [HWT](https://github.com/Nic30/hwt), many example hardware tests can be found in [hwtLib](https://github.com/Nic30/hwtLib) 


# Similar software

* [cocotb](https://github.com/cocotb/cocotb) - there is also WIP version of cocotb-verilator integration
* [cocotb-coverage](https://github.com/mciepluc/cocotb-coverage) - Functional Coverage and Constrained Randomization Extensions for Cocotb 
* [chisel-testers](https://github.com/freechipsproject/chisel-testers)
* [firesim](https://github.com/firesim/firesim)
* [fli](https://github.com/andrepool/fli) - using ModelSim Foreign Language Interface for c – VHDL
* [kratos](https://github.com/Kuree/kratos) - hardware generator/simulator
* [midas](https://github.com/ucb-bar/midas)
* [py-hpi](https://github.com/fvutils/py-hpi) - Python/Simulator integration using procedure calls 
* [PyVSC](https://github.com/fvutils/pyvsc) Python package providing a library for Verification Stimulus and Coverage
* [uvm-python](https://github.com/tpoikela/uvm-python) - cocotb based python UVM

