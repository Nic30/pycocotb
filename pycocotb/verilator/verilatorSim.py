

from contextlib import contextmanager
import distutils
from importlib import machinery
from math import ceil
import multiprocessing.pool
import os
from setuptools import Extension
from setuptools.command.build_ext import build_ext
from setuptools.dist import Distribution
import shutil
from subprocess import check_call
import sys
import tempfile

from jinja2.environment import Environment
from jinja2.loaders import PackageLoader

from pycocotb.verilator.ccompiler_tweaks import monkey_patch_parallel_compilation
from pycocotb.verilator.fs_utils import find_files, working_directory

COCOPY_SRC_DIR = os.path.join(os.path.dirname(__file__), "c_files")
COCOPY_SRCS = [os.path.join(COCOPY_SRC_DIR, "signal_mem_proxy.cpp"), ]
VERILATOR_ROOT = "/usr/local/share/verilator"
VERILATOR_INCLUDE_DIR = os.path.join(VERILATOR_ROOT, "include")
VERILATOR = "verilator_bin_dbg"
template_env = Environment(loader=PackageLoader('pycocotb', "verilator", 'templates'))
verilator_sim_wrapper_template = template_env.get_template(
    'verilator_sim.cpp.template')


def verilatorCompile(files, build_dir):
    files = [files[-1], ]
    cmd = [VERILATOR, "--cc", "--trace", "--Mdir", build_dir] + files
    print(" ".join(cmd))
    try:
        check_call(cmd)
    except Exception as e:
        raise


def getSrcFiles(build_dir, verilator_include_dir):
    build_sources = find_files(build_dir, pattern="*.cpp", recursive=True)
    verilator_sources = [
        verilator_include_dir + "/" + x
        for x in ["verilated.cpp", "verilated_save.cpp", "verilated_vcd_c.cpp"]
    ]
    return [*build_sources, *verilator_sources, *COCOPY_SRCS]


def generatePythonModuleWrapper(top, build_dir, verilator_include_dir, accessible_signals, thread_pool):
    """
    Collect all c/c++ files into setuptools.Extension and build it

    :return: tuple (file name, lib name) file name of builded module (.so/.dll file)
    """

    name = '%s_%d' % (top._name, abs(hash(top)))

    with working_directory(build_dir):
        with open("V" + top._name + "_sim_wrapper.cpp", "w") as f:
            f.write(verilator_sim_wrapper_template.render(
                module_name=name,
                top_name=top._name,
                accessible_signals=accessible_signals))
        sources = getSrcFiles(".", verilator_include_dir)
        with monkey_patch_parallel_compilation(thread_pool):
            dist = Distribution()

            dist.parse_config_files()
            sim = Extension(name,
                            include_dirs=[verilator_include_dir,
                                          build_dir, COCOPY_SRC_DIR],
                            extra_compile_args=['-std=c++17'],
                            # {
                            #    # 'msvc': [],
                            #    'unix': ['-std=c++11'],
                            # },
                            define_macros=[],
                            sources=sources,
                            language="c++",
                            )

            dist.ext_modules = [sim]
            _build_ext = build_ext(dist)
            _build_ext.parallel = 5
            _build_ext.finalize_options()
            _build_ext.run()
            return os.path.join(build_dir, _build_ext.build_lib, sim._file_name), name


if __name__ == "__main__":
    # temporary simple test for components described in HWT framework
    from hwt.hdl.types.bits import Bits
    from hwt.serializer.verilog.serializer import VerilogSerializer
    from hwt.synthesizer.utils import toRtl
    # from hwtLib.amba.axi_comp.axi4_streamToMem import Axi4streamToMem
    from hwtLib.amba.axis_comp.fifo import AxiSFifo
    from ipCorePackager.constants import DIRECTION
    
    def toVerilog(top, build_dir):
        files = toRtl(top, serializer=VerilogSerializer, saveTo=build_dir)
        return files
    
    def collect_signals(top):
        accessible_signals = []
        for p in top._entity.ports:
            t = p._dtype
            if isinstance(t, Bits):
                is_read_only = p.direction == DIRECTION.OUT
                size = ceil(t.bit_length() / 8)
                accessible_signals.append(
                    (p.name, is_read_only, int(bool(t.signed)), size)
                )
        return accessible_signals

    # create instance of component, configure ti and generate unique name
    # u = Axi4streamToMem()
    u = AxiSFifo()
    u.DEPTH.set(128)
    u.DATA_WIDTH.set(128)
    _unique_name = "%s_%s" % (u.__class__.__name__, abs(hash(u)))
    unique_name = u.__class__.__name__
    
    # with tempdir(suffix=unique_name) as build_dir:
    if unique_name:
        build_dir = unique_name
        v_files = toVerilog(u, build_dir)
        accessible_signals = collect_signals(u)

        verilatorCompile(v_files, build_dir)
        with multiprocessing.pool.ThreadPool(multiprocessing.cpu_count()) as thread_pool:
            sim_so, sim_name = generatePythonModuleWrapper(
                u, build_dir, VERILATOR_INCLUDE_DIR, accessible_signals, thread_pool)

            # load compiled library to python
            importer = machinery.FileFinder(os.path.dirname(os.path.abspath(sim_so)),
                                            (machinery.ExtensionFileLoader,
                                             machinery.EXTENSION_SUFFIXES))
            sim = importer.find_module(sim_name).load_module(sim_name)
            sim_cls = getattr(sim, _unique_name)

            # run simulation
            sim = sim_cls()
            print(sim, "sim_prepared")
            for i in range(50):
                print(">", i)
                if i > 10:
                    sim.rst_n.write(1)
                sim.dataIn_data.write(i)
                sim.dataIn_last.write(0)
                sim.dataIn_valid.write(1)
                sim.clk.write(i % 2)
                sim.eval()
                print(sim.dataOut_data.read(), sim.dataOut_last.read(), sim.dataOut_valid.read())

    print("done")
