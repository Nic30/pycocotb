

class Time():
    """
    Time units
    """
    ps = 1
    ns = 1000
    us = ns * 1000
    ms = us * 1000
    s = ms * 1000


# default clk period
# value is not important, it is important that it is always the same.
CLK_PERIOD = 10 * Time.ns
