from typing import List, Union, Tuple

from pycocotb.basic_hdl_simulator.proxy import BasicRtlSimProxy


def sensitivity(
        proc_fn,
        *sensitiveTo: List[Union[BasicRtlSimProxy,
                                 Tuple[Tuple[bool, bool], BasicRtlSimProxy]]]):
    """
    register sensitivity for process
    """
    for s in sensitiveTo:
        if isinstance(s, tuple):
            (rising, falling), s = s
            if rising:
                s.simRisingSensProcs.add(proc_fn)
            if falling:
                s.simFallingSensProcs.add(proc_fn)
            assert rising or falling, s
        else:
            s.simSensProcs.add(proc_fn)


def connectSimPort(sim_unit, sim_sub_unit, unit_port_name: str, sub_unit_port_name: str):
    """
    Connect ports of simulation models by name
    (Replace a child port with a parent signal/port directly)
    """
    newPort = getattr(sim_unit.io, unit_port_name)
    setattr(sim_sub_unit.io, sub_unit_port_name, newPort)
