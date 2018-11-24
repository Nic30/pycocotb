from importlib import machinery
from math import ceil
import multiprocessing
from multiprocessing.pool import ThreadPool
import os

from pycocotb.verilator.simulator import verilatorCompile, \
    generatePythonModuleWrapper, VERILATOR_INCLUDE_DIR


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
    unique_name = u.__class__.__name__
    
    # with tempdir(suffix=unique_name) as build_dir:
    if unique_name:
        build_dir = unique_name
        v_files = toVerilog(u, build_dir)
        accessible_signals = collect_signals(u)

        verilatorCompile(v_files, build_dir)
        with ThreadPool(multiprocessing.cpu_count()) as thread_pool:
            sim_so = generatePythonModuleWrapper(u._name, unique_name,
                build_dir, VERILATOR_INCLUDE_DIR, accessible_signals, thread_pool)

            # load compiled library to python
            importer = machinery.FileFinder(os.path.dirname(os.path.abspath(sim_so)),
                                            (machinery.ExtensionFileLoader,
                                             machinery.EXTENSION_SUFFIXES))
            sim = importer.find_module(unique_name).load_module(unique_name)
            sim_cls = getattr(sim, unique_name)

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
