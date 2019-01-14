from pycocotb.constants import CLK_PERIOD
from pycocotb.triggers import Timer, WriteOnly, Edge
from inspect import isgeneratorfunction


class CallbackLoop(object):
    """
    Simple utility: process which only register other process/function
    as on change callback for specified signal as soon as it is executed.
    """

    def __init__(self, sig: "SimSignal", fn, shouldBeEnabledFn):
        """
        :param sig: signal on which write callback should be used
        :attention: if condFn is None callback function is always executed

        :ivra fn: function/generator which is callback which should be executed
        :ivar isGenerator: flag if callback function is generator
            or normal function
        :ivar shouldBeEnabledFn: function() -> bool, which returns True if this
            callback loop should be enabled
        """
        assert not isinstance(fn, CallbackLoop)
        self.fn = fn
        self.isGenerator = isgeneratorfunction(fn)
        self.shouldBeEnabledFn = shouldBeEnabledFn
        self._callbackIndex = None
        self._enable = True

        try:
            # if sig is interface we need internal signal
            self.sig = sig._sigInside
        except AttributeError:
            self.sig = sig

    def setEnable(self, en, sim):
        self._enable = en

    def __call__(self, sim):
        """
        Process for injecting of this callback loop into simulator
        """
        while True:
            yield Edge(self.sig)
            if self._enable and self.shouldBeEnabledFn():
                if self.isGenerator:
                    yield from self.fn(sim)
                else:
                    self.fn(sim)


class OnRisingCallbackLoop(CallbackLoop):
    """
    Simple utility: process which only register other process/function
    as on rising callback for specified signal as soon as it is executed.
    """

    def __call__(self, sim):
        while True:
            yield Edge(self.sig)
            if self._enable and self.shouldBeEnabledFn():
                yield sim.waitReadOnly()
                if int(self.sig.read()) == 1:
                    if self.isGenerator:
                        yield from self.fn(sim)
                    else:
                        self.fn(sim)


class OnFallingCallbackLoop(CallbackLoop):
    """
    Simple utility: process which only register other process/function
    as on falling callback for specified signal as soon as it is executed.
    """

    def __call__(self, sim):
        while True:
            yield Edge(self.sig)
            if self._enable and self.shouldBeEnabledFn():
                yield sim.waitReadOnly()
                if int(self.sig.read()) == 0:
                    if self.isGenerator:
                        yield from self.fn(sim)
                    else:
                        self.fn(sim)

