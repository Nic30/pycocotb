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


def connectSimPort(simUnit, subSimUnit, srcName, dstName, dir_to_subcomponent):
    """
    Connect ports of simulation models by name
    """
    if dir_to_subcomponent:
        newPort = getattr(simUnit.io, srcName)
        setattr(subSimUnit.io, dstName, newPort)
    else:
        newPort = getattr(simUnit.io, dstName)
        setattr(subSimUnit.io, srcName, newPort)
