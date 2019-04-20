from os.path import dirname, abspath, join
from pycocotb.verilator.simulator_gen import verilatorCompile, \
    generatePythonModuleWrapper, loadPythonCExtensionFromFile

VERILOG_SRCS = dirname(abspath(__file__))


def format_accessible_signals(accessible_signals, top_name):
    _accessible_signals = []
    for signal_name, read_only, is_signed, type_width in  accessible_signals:
        # name as tuple, add top_name if is hierarchical
        if isinstance(signal_name, str):
            signal_phy_name = signal_name = (signal_name,)
        elif len(signal_name) > 1:
            signal_phy_name = (top_name, *signal_name)
        else:
            signal_phy_name = signal_name

        signal_phy_name = "__DOT__".join(signal_phy_name)

        read_only = int(read_only)
        is_signed = int(is_signed)
        if isinstance(type_width, int):
            type_width = (type_width,)

        _accessible_signals.append((signal_name, signal_phy_name, read_only, is_signed, type_width))       

    return _accessible_signals

    
def build_sim(verilog_files, accessible_signals, tc, build_dir, top_name):
    sim_verilog = [join(VERILOG_SRCS, f) for f in verilog_files]
    verilatorCompile(sim_verilog, build_dir)

    accessible_signals = format_accessible_signals(accessible_signals, top_name)
    module_file_name = generatePythonModuleWrapper(
        top_name, top_name,
        build_dir,
        accessible_signals)

    sim_module = loadPythonCExtensionFromFile(module_file_name, top_name)
    sim_cls = getattr(sim_module, top_name)

    simInstance = sim_cls()
    io = simInstance.io
    for sigName, sigPhyName, _, _, _ in accessible_signals:
        _io = io
        for n in sigName:
            _io = getattr(_io, n)
        tc.assertEqual(_io.name, sigName[-1])

    return simInstance
