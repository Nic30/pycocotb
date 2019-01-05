# PyCOCOTB

[![Build Status](https://travis-ci.org/Nic30/pycocotb.svg?branch=master)](https://travis-ci.org/Nic30/pycocotb)
[![Build status](https://ci.appveyor.com/api/projects/status/oy1ciuqhuax6vt4u?svg=true)](https://ci.appveyor.com/project/nic30/pycocotb)
[![Coverage Status](https://coveralls.io/repos/github/Nic30/pycocotb/badge.svg?branch=master)](https://coveralls.io/github/Nic30/pycocotb?branch=master)

[COCOTB](https://github.com/potentialventures/cocotb) like HDL simulation environment where simulation is driven from Python. 
Simulation is just an object instance and can be manipulated as any other object.
This allows better code reuse, integration with existing test frameworks and better test automation.


# Installation

## Linux

* `sudo apt install build-essential python3 cmake flex bison git libboost-dev libboost-all-dev` 
* download [verilator](https://www.veripool.org/projects/verilator/wiki/Installing)
* apply patches from `verilator_patches_tmp` (`cd verilator; git am ../verilator_patches_tmp/*.patch`)
* install verilator
* run `sudo python3 setup.py install` to install globally or `python3 setup.py install --user` to install to `~/.local/...`
* Or if you want to just test this library without any kind of installation use `python3 setup.py build` to build c extensions.

## Windows

* install [Python 3](https://www.python.org/downloads/)
* install [Visual Studio](https://visualstudio.microsoft.com/thank-you-downloading-visual-studio/?sku=Community&rel=15) (C++)
* install [CMake](https://cmake.org/)
* install [boost](https://www.boost.org/doc/libs/1_69_0/more/getting_started/windows.html)
* install [Cygwin](https://cygwin.com/install.html) and save installer `setup-x86_64.exe` to cygwin root. 
* use `ci_scripts/appveyor_install.sh` to install this library and it's dependencies 

After installation verilator has to run under cygwin, but python and this library are not restricted.


# Current state
* alfa
* experimental Python <-> Verilator binding, experimental UVM like environment
* some examples in tests


# Similar software

* [midas](https://github.com/ucb-bar/midas)
* [firesim](https://github.com/firesim/firesim)
