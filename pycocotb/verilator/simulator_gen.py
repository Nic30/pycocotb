

from multiprocessing.pool import ThreadPool
import os
from setuptools import Extension
from setuptools.command.build_ext import build_ext
from setuptools.dist import Distribution
from subprocess import check_call
import sys
from typing import List, Dict

from jinja2.environment import Environment
from jinja2.loaders import PackageLoader

from pycocotb.verilator.ccompiler_tweaks import monkey_patch_parallel_compilation
from pycocotb.verilator.fs_utils import find_files, working_directory

COCOPY_SRC_DIR = os.path.join(os.path.dirname(__file__), "c_files")
COCOPY_SRCS = [os.path.join(COCOPY_SRC_DIR, "signal_mem_proxy.cpp"), ]
VERILATOR_ROOT = "/usr/local/share/verilator"
VERILATOR_INCLUDE_DIR = os.path.join(VERILATOR_ROOT, "include")
VERILATOR = "verilator_bin_dbg"

template_env = Environment(loader=PackageLoader("pycocotb", "verilator/templates"))
verilator_sim_wrapper_template = template_env.get_template(
    'verilator_sim.cpp.template')
DEFAULT_EXTENSION_EXTRA_ARGS = {"extra_compile_args": ['-std=c++17']}


def verilatorCompile(files: List[str], build_dir:str):
    files = [files[-1], ]
    cmd = [VERILATOR, "--cc", "--trace", "--Mdir", build_dir] + files
    try:
        check_call(cmd)
    except Exception:
        print(" ".join(cmd), file=sys.stderr)
        raise


def getSrcFiles(build_dir:str, verilator_include_dir:str):
    build_sources = find_files(build_dir, pattern="*.cpp", recursive=True)
    verilator_sources = [
        verilator_include_dir + "/" + x
        for x in ["verilated.cpp", "verilated_save.cpp", "verilated_vcd_c.cpp"]
    ]
    return [*build_sources, *verilator_sources, *COCOPY_SRCS]


def generatePythonModuleWrapper(top_name:str, top_unique_name:str, build_dir:str,
                                verilator_include_dir:str,
                                accessible_signals, thread_pool:ThreadPool,
                                extra_Extension_args:Dict[str, object]=DEFAULT_EXTENSION_EXTRA_ARGS):
    """
    Collect all c/c++ files into setuptools.Extension and build it

    :param top_name: name of top in simulation
    :param top_unique_name: unique name used as name for simulator module
    :param build_dir: tmp directory where simulation should be build
    :param verilator_include_dir: include directory of velilator

    :return: file name of builded module (.so/.dll file)
    """
    with working_directory(build_dir):
        with open("V" + top_name + "_sim_wrapper.cpp", "w") as f:
            f.write(verilator_sim_wrapper_template.render(
                module_name=top_unique_name,
                top_name=top_name,
                accessible_signals=accessible_signals))
        sources = getSrcFiles(".", verilator_include_dir)
        with monkey_patch_parallel_compilation(thread_pool):
            dist = Distribution()

            dist.parse_config_files()
            sim = Extension(top_unique_name,
                            include_dirs=[verilator_include_dir,
                                          build_dir, COCOPY_SRC_DIR],
                            sources=sources,
                            language="c++",
                            **extra_Extension_args,
                            )

            dist.ext_modules = [sim]
            _build_ext = build_ext(dist)
            _build_ext.finalize_options()
            _build_ext.run()
            return os.path.join(build_dir, _build_ext.build_lib, sim._file_name)
