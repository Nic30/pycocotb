from pycocotb.basic_hdl_simulator.basicSimIo import BasicSimIo


class BasicSimModel(object):
    """
    Base class for model in simulator
    """

    def __init__(self, name=None):
        self._name = name
        self.io = BasicSimIo()
        self._interfaces = []
        self._processes = []
        self._units = []
        self._outputs = {}
