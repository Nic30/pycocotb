"""
Agents for UART (COM, serial, Universal Asynchronous Receiver-Transmitter) interface

As this interface is asynchronous it does not need care clock signals or resets.
And BAUD has to be set correctly for correct functionality.
"""
from collections import deque
from typing import Tuple

from pycocotb.agents.base import AgentBase
from pycocotb.constants import Time
from pycocotb.hdlSimulator import HdlSimulator
from pycocotb.triggers import Timer, WaitTimeslotEnd


# constants for most common baud rates
BAUD_9600 = 9600
BAUD_19200 = 19200
BAUD_38400 = 38400
BAUD_57600 = 57600
BAUD_115200 = 115200
# constant which should be use when same baud is required but value is not important
BAUD_DEFAULT = BAUD_115200


class UartDataAgent(AgentBase):
    """
    :ivar ~.char_buff: the buffer used for bits while sending the character
    """
    START_BIT = 0
    STOP_BIT = 1

    def __init__(self, sim: HdlSimulator, intf: "RtlSignal", baud: int):
        super(UartDataAgent, self).__init__(sim, intf)
        self.set_baud(self, baud)
        self.char_buff = []
        self.data = deque()

    def set_baud(self, baud: int):
        self.bit_period = Time.s // baud
        assert self.bit_period > 2, baud

    def recieve_text(self) -> str:
        """
        :return: data of this agent (collected form interface) as str
        """

    def send_text(self, text: str):
        """
        Add text to agent data (agent will send it as soon as ready)
        """

    def monitor(self):
        half_period = Timer(self.bit_period // 2)
        period = Timer(self.bit_period)
        intf = self.intf

        yield half_period

        while True:
            while True:
                if not self.getEnable():
                    yield period
                    continue

                yield WaitTimeslotEnd()
                d = intf.read()
                if int(d) == self.START_BIT:
                    break
                else:
                    yield half_period

            for _ in range(8):
                yield period
                yield WaitTimeslotEnd()
                d = intf.read()
                self.char_buff.append(d)

            d = int(d)
            if d == self.STOP_BIT:
                # correctly received char
                self.char_buff.clear()
                ch = 0
                for b in reversed(self.char_buff):
                    ch <<= 1
                    ch |= int(b)
                yield period
            else:
                # received data is in wrong format, discard it
                self.char_buff.clear()
                yield half_period

    def driver(self):
        half_period = Timer(self.bit_period // 2)
        period = Timer(self.bit_period)
        intf = self.intf
        yield half_period
        while True:
            if self.getEnable() and self.data:
                ch = self.data.popleft()
                intf.write(self.START_BIT)
                yield period
                for i in range(8):
                    intf.write((ch >> i) & 0b1)
                    yield period
                intf.write(self.STOP_BIT)
            yield period


class UartRxTxAgent(AgentBase):

    def __init__(self, intf: Tuple["RtlSignal", "RtlSignal"], baud: int):
        super(UartRxTxAgent, self).__init__(intf)
        rx, tx = intf
        self.rx = UartDataAgent(rx, baud)
        self.tx = UartDataAgent(tx, baud)

    def set_baud(self, baud: int):
        self.rx.set_baud(baud)
        self.tx.set_baud(baud)

    def getDrivers(self):
        return (
            *self.rx.getMonitors(),
            *self.tx.getDrivers(),
        )

    def getMonitors(self):
        return (
            *self.rx.getDrivers(),
            *self.tx.getMonitors(),
        )
