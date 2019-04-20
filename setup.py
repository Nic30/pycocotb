import os
from setuptools import setup
from setuptools.extension import Library


COCOPY_SRC_DIR = os.path.join(
    os.path.dirname(__file__),
    "pycocotb", "verilator", "c_files")
COCOPY_SRCS = [os.path.join(COCOPY_SRC_DIR, "signal_mem_proxy.cpp"),
               os.path.join(COCOPY_SRC_DIR, "sim_io.cpp"),
               os.path.join(COCOPY_SRC_DIR, "pycocotb_sim.cpp") ]
VERILATOR_ROOT = "/usr/local/share/verilator"
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

setup(
    name='pycocotb',
    version='0.1',
    author='',
    install_requires=[
        "jinja2",  # template engine
    ],
    author_email='michal.o.socials@gmail.com',
    ext_modules=[verilator_common],
)
