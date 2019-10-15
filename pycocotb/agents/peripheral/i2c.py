from collections import deque
from typing import Tuple, Deque, Union, Optional

from pycocotb.agents.base import AgentWitReset, NOP, RX, TX
from pycocotb.agents.peripheral.tristate import TristateAgent, TristateClkAgent
from pycocotb.triggers import WaitCombStable, WaitWriteOnly, WaitCombRead,\
    WaitAllStable
from enum import Enum
from pycocotb.hdlSimulator import HdlSimulator

TRI_STATE_SIG_T = Tuple["RtlSignal", "RtlSignal", "RtlSignal"]  # i, o, t


class I2C_MODE(Enum):
    STANDARD = 100000
    FAST = 400000
    HIGH_SPEED = 3400000


class I2C_ADDR(Enum):
    ADDR_7b = 7
    ADDR_10b = 10


def getBit(val, bitNo):
    """
    get specific bit from integer (little-endian)
    """
    return (val >> bitNo) & 1


class I2cAgent(AgentWitReset):
    """
    A base simulation agent for I2C interfaces. Note that as all devices are using tri-state interfaces.
    The agent has to know the data format which of device in order to interpret data correctly.
    https://www.nxp.com/docs/en/user-guide/UM10204.pdf
    https://dlbeer.co.nz/articles/i2c.html

    The agent will support slave mode after it's address is set

    Master agent transaction formats:
          [((READ, ACK/NACK) | (WRITE, VALUE, ACK/NACK) | (REPEATED_START, duration in I2C clk))*]
          (ACK/NACK values are there to check the slave response)
    Slave agent uses the onWrite/onRead callbacks

    :attention: multi-master arbitration not implemented
    :note: The driver/monitor difference is related to directions of signals but as the used interface
        is tri-state interface bouth agents can be SLAVE/master
    :note: typical I2C command: START, A6-0, R/W, ACK,  ...  D7-0, ACK, STOP
    :note: each agent is master, but none is active if it does not have transactions to do so
    :note: slave has to check address in function because some devices may actually use
        part of address as opt code etc. because of this this agent needs to be more generic

    :ivar data_m: the buffer for transaction for master
    :ivar data_m_read: the buffer for readed data by master
    :ivar start: flag, if True the master should send I2C START
    :ivar stop: flag, if True the master should send I2C STOP

    :ivar bit_cntrl: the buffer for commands for specific SDA value
                    (intermediate instructions)
    :ivar bit_cntrl_rx: the buffer for a bit values of SDA
                    (intermediate read value)
    """

    ADDR_PREFIX_10b = 0b11110000

    ACK = 0  # send by reciever
    NACK = 1

    READ = 1
    WRITE = 0

    START = "START"
    RESTART = START
    STOP = "STOP"

    def __init__(self, sim: HdlSimulator, intf: Tuple[TRI_STATE_SIG_T, TRI_STATE_SIG_T],
                 rst: Tuple["RtlSignal", bool],
                 MODE=I2C_MODE.STANDARD,
                 ADDR_BITS=I2C_ADDR.ADDR_7b):
        """
        :param: intf i2c interface, tuple (scl, sda) = (clock, data),
            sda/sdc are tri-state interfaces represented by i, o, t signals
        """
        AgentWitReset.__init__(self, sim, intf, rst)
        self.data_m = deque()
        self.data_m_read = []
        self.bit_cntrl: Deque[Tuple[
                                Union[RX, TX],
                                Optional[int]
                                ]] = deque()
        self.bit_cntrl_rx: List[int] = []
        self.start = True
        self.sda = TristateAgent(sim, intf[1], rst)
        self.sda.collectData = False
        self.sda.selfSynchronization = False
        self.slave = False
        self.mode = MODE
        self.addr_bits = ADDR_BITS

    def _transmit_byte(self, val: int, ack_for_check: Optional[bool]):
        for i in range(8):
            b = getBit(val, 7-i)
            self.bit_cntrl.append((TX, b))
        self.bit_cntrl.append((RX, ack_for_check))
        yield from self._wait_until_command_completion()
        assert len(self.bit_cntrl_rx) == 1
        return self.bit_cntrl_rx.pop()

    def _receive_byte(self, ack: bool):
        """
        :note: If master is a reciever the ack means that it wishes to recieve next byte
        """
        for _ in range(8):
            self.bit_cntrl.append((RX, None))
        self.bit_cntrl.append((TX, int(ack)))
        yield from self._wait_until_command_completion()
        assert len(self.bit_cntrl_rx) == 8
        b = 0
        for _b in self.bit_cntrl_rx:
            b <<= 1
            b |= _b
        return b

    def _wait_until_command_completion(self):
        # wait untill command get processed
        while self.bit_cntrl:
            yield WaitCombRead()
            if self.bit_cntrl:
                yield WaitAllStable()

    def execute_master_transaction(self):
        trans = self.data.pop()
        for t in trans:
            m = t[0]
            if m == RX:
                b = yield from self._receive_byte(t[1])
                raise NotImplementedError(b)
            elif m == TX:
                ack = yield from self._transmit_byte(b[1], b[2])
                raise NotImplementedError(ack)
            elif m == self.START:
                raise NotImplementedError()
            elif m == self.STOP:
                raise NotImplementedError()
            else:
                ValueError(m)
        self.stop = True

    def execute_slave_transaction(self):
        if self.ADDR_BITS == I2C_ADDR.ADDR_7b:
            yield from self._receive_byte(1)
            addr = self.data_rx.pop()
            rw = addr & 0b1
            addr >>= 1
        elif self.ADDR_BITS == I2C_ADDR.ADDR_10b:
            yield from self._receive_byte(1)
            addrLow = self.data_rx.pop()
            addrLow = int(addrLow)
            rw = addrLow & 0b1
            addrLow >>= 1
            assert addr & 0b11111000 == self.ADDR_PREFIX_10b
            yield from self._receive_byte(1)
            addrHigh = self.data_rx.pop()
            addrHigh = int(addrHigh)
            addr = (addr << 8) | addrHigh

    def startListener(self):
        # SDA->0 and SCL=1
        if self.start:
            self.bits.append(self.START)
            self.start = False
            yield self.execute_master_transaction()

        return
        yield

    def startSender(self, sim):
        # SDA->0 and SCL=1
        if self.start:
            self.sda._write(0)
            self.start = False

        return
        yield

    def getMonitors(self):
        self.scl = TristateClkAgent(
            self.intf[0], self.rst, self.rstOffIn,
            onRisingCallback=self.monitor,
            onFallingCallback=self.startListener
        )
        return (
            *self.sda.getMonitors(),
            *self.scl.getMonitors()
        )

    def getDrivers(self):
        self.scl = TristateClkAgent(
            self.intf[0], self.rst, self.rstOffIn,
            onRisingCallback=self.driver,
            onFallingCallback=self.startSender
        )
        self.scl.setEnable(False, None)
        return (
            self.driver,  # initialization of the interface
            * self.sda.getDrivers(),
            *self.scl.getDrivers()
        )

    def monitor(self, sim):
        # now intf.sdc is rising
        yield WaitCombStable()
        # wait on all agents to update values and on
        # simulator to apply them
        if sim.now > 0 and self.notReset(sim):
            for _ in range(8):
                v = self.sda.i.read()
                self.bits.append(v)
            self.sda._write(self.ACK)

    def driver(self, sim):
        # now intf.sdc is rising
        # prepare data for next clk
        yield WaitWriteOnly()
        if self.bits:
            b = self.bits.popleft()
            if b == self.START:
                self.start = True
                return
            elif b == self.STOP:
                self.stop = True
                return
        else:
            b = NOP

        self.sda._write(b)

    def setEnable(self, en, sim):
        """
        """
        # If there is no pending transaction no pause is required
        if not self.start and not self.stop and not self.bit_cntrl:
            super(I2cAgent, self).setEnable(en, sim)
        else:
            # wait until clock
            raise NotImplementedError()
