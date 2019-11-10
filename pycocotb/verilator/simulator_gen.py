

from copy import deepcopy
from distutils.sysconfig import get_config_var
from importlib import machinery
from jinja2.environment import Environment
from jinja2.loaders import PackageLoader
import os
from os.path import dirname
import  platform
from setuptools import Extension
from setuptools.command.build_ext import build_ext
from setuptools.dist import Distribution
from subprocess import check_call
import sys
from typing import List, Dict, Tuple

from pycocotb.verilator.fs_utils import find_files, working_directory


VER_SIM_GEN_BASE = os.path.dirname(__file__)
COCOPY_SRC_DIR = os.path.join(VER_SIM_GEN_BASE, "c_files")
VERILATOR_ROOT = "/usr/local/share/verilator"
VERILATOR_INCLUDE_DIR = os.path.join(VERILATOR_ROOT, "include")
VERILATOR = "verilator_bin_dbg"

template_env = Environment(
    loader=PackageLoader("pycocotb", "verilator/templates")
)
verilator_sim_wrapper_template = template_env.get_template(
    'verilator_sim.cpp.template')

# "cpython-36m-x86_64-linux-gnu"
SOABI = get_config_var("SOABI")
# e.g. "linux"
MACHDEP = get_config_var("MACHDEP")
# e.g. "x86_64"
AR = platform.processor()
# e.g. "3.6"
VERSION = get_config_var("VERSION")

IN_PLACE_LIB_DIR = os.path.abspath(
    os.path.join(
        VER_SIM_GEN_BASE,
        "..",
        "..",
        "build",
        "lib.%s-%s-%s" % (MACHDEP, AR, VERSION),
        "pycocotb",
        "verilator"))
INSTALLED_LIB_DIR = os.path.join(VER_SIM_GEN_BASE)


DEFAULT_EXTENSION_EXTRA_ARGS = {
    "extra_compile_args": ['-std=c++17'],
    "libraries": ["boost_coroutine", "boost_context", "boost_system",
                  "common." + SOABI],
    "include_dirs": [VERILATOR_INCLUDE_DIR, COCOPY_SRC_DIR],
    "language": "c++",
    "library_dirs": [IN_PLACE_LIB_DIR, INSTALLED_LIB_DIR],
    "extra_compile_args": [
        "-std=c++11",
        # "-faligned-new"
    ],
}


def verilatorCompile(files: List[str], build_dir: str):
    include_dirs = ["-I%s" % dn
                    for dn in set(dirname(f)
                                  for f in files)
                    if dn and dn != "."]
    files = [files[-1], ]
    cmd = [VERILATOR, "--cc", "--event-triggers",
           "--trace", "--Mdir", build_dir] + files + include_dirs
    try:
        check_call(cmd)
    except Exception:
        print(" ".join(cmd), file=sys.stderr)
        raise


def getSrcFiles(build_dir: str):
    build_sources = find_files(build_dir, pattern="*.cpp", recursive=True)
    return [*build_sources]


def generatePythonModuleWrapper(
        top_name: str, top_unique_name: str,
        build_dir: str,
        accessible_signals: List[Tuple[str, bool, bool, int]],
        extra_Extension_args: Dict[str, object]=DEFAULT_EXTENSION_EXTRA_ARGS):
    """
    Collect all c/c++ files into setuptools.Extension and build it

    :param top_name: name of top in simulation
    :param top_unique_name: unique name used as name for simulator module
    :param build_dir: tmp directory where simulation should be build
    :param verilator_include_dir: include directory of Verilator
    :param accessible_signals: List of tuples (signal_name, signal_phy_name, read_only, is_signed, type_width)
    :param extra_Extension_args: additional values for setuptools.Extension constructor

    :return: file name of builded module (.so/.dll file)
    """
    with working_directory(build_dir):
        with open("V" + top_name + "_sim_wrapper.cpp", "w") as f:
            f.write(verilator_sim_wrapper_template.render(
                module_name=top_unique_name,
                top_name=top_name,
                accessible_signals=accessible_signals))
        sources = getSrcFiles(".")
        dist = Distribution()

        dist.parse_config_files()

        extra_Extension_args = deepcopy(extra_Extension_args)
        extra_Extension_args["sources"] = extra_Extension_args.get("sources", []) + sources
        extra_Extension_args["include_dirs"] = extra_Extension_args.get("include_dirs", []) + [build_dir, ]

        sim = Extension(top_unique_name,
                        **extra_Extension_args,
                        )

        dist.ext_modules = [sim]
        _build_ext = build_ext(dist)
        _build_ext.finalize_options()
        _build_ext.run()
        return os.path.join(build_dir, _build_ext.build_lib,
                            sim._file_name)


def loadPythonCExtensionFromFile(library_file_name: str, module_name: str):
    importer = machinery.FileFinder(
        os.path.dirname(os.path.abspath(library_file_name)),
        (machinery.ExtensionFileLoader,
         machinery.EXTENSION_SUFFIXES))
    module = importer.find_module(module_name).load_module(module_name)
    return module
