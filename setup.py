import os
from setuptools import setup, find_packages
from setuptools.extension import Library
import sys
from os import path

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


this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='pycocotb',
    version='1.0',
    description='RTL simulator API',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author_email='michal.o.socials@gmail.com',
    install_requires=[
        "jinja2",  # template engine
        "sortedcontainers",  # for calendar queue in simulator
        "pyMathBitPrecise>=0.8",  # bit precise integer types for sim
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)",
        "Topic :: System :: Hardware",
        "Topic :: System :: Emulators",
        "Topic :: Utilities"],
    license='MIT',
    packages=find_packages(),
    package_data={'pycocotb.verilator': ['*.h', '*.cpp', '*.template']},
    include_package_data=True,
    zip_safe=False,
    ext_modules=ext_modules,
    test_suite="pycocotb.tests.all.suite"
)
