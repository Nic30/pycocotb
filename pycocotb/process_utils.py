from pycocotb.constants import CLK_PERIOD
from pycocotb.triggers import Timer, WriteOnly
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
        self.__enable = True

        try:
            # if sig is interface we need internal signal
            self.sig = sig._sigInside
        except AttributeError:
            self.sig = sig

    def setEnable(self, en, sim):
        self.__enable = en

    def onWriteCallback(self, sim):
        if self.__enable and self.shouldBeEnabledFn():
            if self.isGenerator:
                yield from self.fn(sim)
            else:
                self.fn(sim)

    def __call__(self, sim):
        """
        Process for injecting of this callback loop into simulator
        """
        self.sig.registerOnChangeCallback(self.onWriteCallback)
        return
        yield


class OnRisingCallbackLoop(CallbackLoop):
    """
    Simple utility: process which only register other process/function
    as on rising callback for specified signal as soon as it is executed.
    """

    def onWriteCallback(self, sim):
        if self.__enable and self.shouldBeEnabledFn() and int(self.sig) == 1:
            if self.isGenerator:
                yield from self.fn(sim)
            else:
                self.fn(sim)


class OnFallingCallbackLoop(CallbackLoop):
    """
    Simple utility: process which only register other process/function
    as on falling callback for specified signal as soon as it is executed.
    """

    def onWriteCallback(self, sim):
        if self.__enable and self.shouldBeEnabledFn()\
                and int(self.sig.read()) == 0:
            if self.isGenerator:
                yield from self.fn(sim)
            else:
                self.fn(sim)


def oscilate(sig, period=CLK_PERIOD, initWait=0):
    """
    Oscillative simulation driver for your signal
    (usually used as clk generator)
    """

    def oscillateStimul(s):
        s.write(False, sig)
        halfPeriod = period / 2.0
        yield Timer(initWait)

        wrOnly = WriteOnly()
        while True:
            yield s.wait(halfPeriod)
            yield wrOnly
            s.write(True, sig)

            yield Timer(halfPeriod)
            yield wrOnly
            s.write(False, sig)

    return oscillateStimul
