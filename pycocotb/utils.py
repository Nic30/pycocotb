from pycocotb.constants import Time


def freq_to_period(f):
    return (Time.s / f)
