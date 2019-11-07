import os
from setuptools import setup, find_packages
from setuptools.extension import Library
import sys

ext_modules = []

if "--verilator" in sys.argv:
    sys.argv.remove("--verilator")

    COCOPY_SRC_DIR = os.path.join(
        os.path.dirname(__file__),
        "pycocotb", "verilator", "c_files")
    COCOPY_SRCS = [os.path.join(COCOPY_SRC_DIR, p)
                   for p in [
                             "signal_mem_proxy.cpp",
                             "signal_array_mem_proxy.cpp",
                             "sim_io.cpp",
                             "pycocotb_sim.cpp"]
                   ]
    #VERILATOR_ROOT = "/usr/local/share/verilator"
    VERILATOR_ROOT = "./verilator"

    VERILATOR_INCLUDE_DIR = os.path.join(VERILATOR_ROOT, "include")
    VERILATOR_SOURCES = [
        os.path.join(VERILATOR_INCLUDE_DIR, x)
        for x in ["verilated.cpp", "verilated_save.cpp", "verilated_vcd_c.cpp"]
    ]

    verilator_common = Library(
        "pycocotb.verilator.common",
        sources=COCOPY_SRCS + VERILATOR_SOURCES,
        extra_compile_args=["-std=c++11", "-I" + VERILATOR_INCLUDE_DIR],
    )
    ext_modules.append(verilator_common)

setup(
    name='pycocotb',
    version='0.1',
    author_email='michal.o.socials@gmail.com',
    install_requires=[
        "jinja2",  # template engine
        "sortedcontainers",  # for calendar queue in simulator
    ],
    license='MIT',
    packages=find_packages(),
    package_data={'pycocotb.verilator': ['*.h', '*.cpp', '*.template']},
    include_package_data=True,
    zip_safe=False,
    ext_modules=ext_modules,
    test_suite="pycocotb.tests.all.suite"
)
