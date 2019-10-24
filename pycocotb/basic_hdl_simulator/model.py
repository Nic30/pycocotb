from pycocotb.basic_hdl_simulator.io import BasicRtlSimIo


class BasicRtlSimModel(object):
    """
    Base class for model in simulator
    """

    def __init__(self, name=None):
        self._name = name
        self.io = BasicRtlSimIo()
        self._interfaces = []
        self._processes = []
        self._units = []
        self._outputs = {}
