from inspect import isgeneratorfunction

from pycocotb.hdlSimulator import HdlSimulator
from pycocotb.triggers import Edge, WaitCombRead


class CallbackLoop(object):
    """
    Simple utility: process which only register other process/function
    as on change callback for specified signal as soon as it is executed.
    """

    def __init__(self, sim: HdlSimulator, sig: "RtlSignal", fn, shouldBeEnabledFn):
        """
        :param sig: signal on which write callback should be used
        :attention: if condFn is None callback function is always executed

        :ivra fn: function/generator which is callback which should be executed
        :ivar ~.isGenerator: flag if callback function is generator
            or normal function
        :ivar ~.shouldBeEnabledFn: function() -> bool, which returns True if this
            callback loop should be enabled
        :ivar ~.pre_init: if True the 'fn' is executed once imidiately for an intialization
            before any callback is triggered
        """
        assert not isinstance(fn, CallbackLoop)
        self.sim = sim
        self.fn = fn
        self.isGenerator = isgeneratorfunction(fn)
        self.shouldBeEnabledFn = shouldBeEnabledFn
        self._callbackIndex = None
        self._enable = True
        self.sig = sig
        self.pre_init = False

    def setEnable(self, en):
        self._enable = en

    def __call__(self):
        """
        Process for injecting of this callback loop into simulator
        """
        if self.pre_init:
            yield from self.fn()

        while True:
            yield Edge(self.sig)
            if self._enable and self.shouldBeEnabledFn():
                if self.isGenerator:
                    yield from self.fn()
                else:
                    self.fn()


class OnRisingCallbackLoop(CallbackLoop):
    """
    Simple utility: process which only register other process/function
    as on rising callback for specified signal as soon as it is executed.
    """

    def __call__(self):
        if self.pre_init:
            yield from self.fn()

        while True:
            yield Edge(self.sig)
            if self._enable and self.shouldBeEnabledFn():
                yield WaitCombRead()
                if int(self.sig.read()) == 1:
                    if self.isGenerator:
                        yield from self.fn()
                    else:
                        self.fn()


class OnFallingCallbackLoop(CallbackLoop):
    """
    Simple utility: process which only register other process/function
    as on falling callback for specified signal as soon as it is executed.
    """

    def __call__(self):
        if self.pre_init:
            yield from self.fn()

        while True:
            yield Edge(self.sig)
            if self._enable and self.shouldBeEnabledFn():
                yield WaitCombRead()
                if int(self.sig.read()) == 0:
                    if self.isGenerator:
                        yield from self.fn()
                    else:
                        self.fn()

