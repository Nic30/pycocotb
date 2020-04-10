from collections import deque
from typing import Tuple, Union, Optional

from pycocotb.agents.base import AgentWitReset, NOP, RX, TX
from pycocotb.agents.peripheral.tristate import TristateAgent, TristateClkAgent,\
    TristateSignal
from pycocotb.triggers import WaitCombStable, WaitWriteOnly, WaitCombRead,\
    WaitTimeslotEnd
from enum import Enum
from pycocotb.hdlSimulator import HdlSimulator
from pycocotb.process_utils import OnRisingCallbackLoop, OnFallingCallbackLoop


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

    :note: The agent will support slave mode after it's address is set.

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

    :ivar ~.data_m: the buffer for transaction for master
    :ivar ~.data_m_read: the buffer for read data by master
    :ivar ~.start: flag, if True the master should send I2C START
    :ivar ~.stop: flag, if True the master should send I2C STOP

    :ivar ~.bit_cntrl: the buffer for commands for specific SDA value
                    (intermediate instructions)
    :ivar ~.bit_cntrl_rx: the buffer for a bit values of SDA
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

    def __init__(self, sim: HdlSimulator, intf: Tuple[TristateSignal, TristateSignal],
                 rst: Tuple["RtlSignal", bool]):
        """
        :param: intf i2c interface, tuple (scl, sda) = (clock, data),
            sda/sdc are tri-state interfaces represented by i, o, t signals
        """
        AgentWitReset.__init__(self, sim, intf, rst)
        self.data_m = deque()
        self.data_m_read = []
        self.bit_cntrl = deque()  # type: Deque[ Tuple[Union[RX, TX], Optional[int]] ]
        self.bit_cntrl_rx = deque()  # type: Deque[Union[START, STOP, int]]
        self.start = True
        self.sda = TristateAgent(sim, intf[1], rst)
        self.sda.collectData = False
        self.sda.selfSynchronization = False
        self.slave = False
        self.bit_index = None

    def hasTransactionPending(self):
        return (
            self.data_m
            or self.data_m_read
            or self.bit_cntrl
            or self.bit_cntrl_rx)

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
                yield WaitTimeslotEnd()

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

    def monitor_on_read(self, addr):
        raise NotImplementedError()
    def monitor_on_write(self, addr):
        raise NotImplementedError()

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

        if rw == self.READ:
            yield from self.monitor_on_read(addr)
        else:
            yield from self.monitor_on_write(addr)

    def startListener(self):
        # SDA->0 and SCL=1
        if self.start:
            self.bit_index = 0
            self.bit_cntrl_rx.append(self.START)
            self.start = False
            # yield sexecute_master_transactionelf.execute_master_transaction()

        return
        yield

    def startSender(self):
        # SDA->0 and SCL=1
        if self.start:
            self.bit_index = 0
            self.sda._write(0)
            self.start = False

        return
        yield

    def getMonitors(self):
        sim = self.sim
        scl = self.intf[0]
        self.scl = TristateClkAgent(
            sim, scl, (self.rst, self.rstOffIn),
        )
        self.monitor = OnRisingCallbackLoop(
            sim, scl.i, self.monitor, self.getEnable)
        self.startListener = OnFallingCallbackLoop(
            sim, scl.i, self.startListener, self.getEnable)

        return (
            self.monitor(),
            self.startListener(),
            *self.sda.getMonitors(),
            *self.scl.getMonitors()
        )

    def getDrivers(self):
        sim = self.sim
        scl = self.intf[0]
        driver = self.driver
        self.scl = TristateClkAgent(
            sim, scl, (self.rst, self.rstOffIn),
        )
        self.driver = OnRisingCallbackLoop(
            sim, scl.i, self.driver, self.getEnable)
        self.startSender = OnFallingCallbackLoop(
            sim, scl.i, self.startSender, self.getEnable)
        self.scl.setEnable(False, None)
        return (
            driver(),  # initialization of the interface
            self.driver(),
            self.startSender(),
            *self.sda.getDrivers(),
            *self.scl.getDrivers()
        )

    def monitor(self):
        # now intf.sdc is rising
        yield WaitCombRead()
        # wait on all agents to update values and on
        # simulator to apply them
        if self.sim.now > 0 and self.notReset():
            if self.bit_index != 8:
                self.bit_index += 1
                yield WaitCombStable()
                v = self.sda.i.read()
                self.bit_cntrl_rx.append(v)
            else:
                yield WaitWriteOnly()
                self.sda._write(self.ACK)

    def driver(self):
        # now intf.sdc is rising
        # prepare data for next clk
        yield WaitWriteOnly()
        if self.bits:
            b = self.bits.popleft()
            if b == self.START:
                self.start = True
                return
            elif b == self.STOP:
                self.bit_index = None
                self.stop = True
                return
        else:
            b = NOP

        self.sda._write(b)

    def setEnable(self, en):
        """
        """
        # If there is no pending transaction no pause is required
        if not self.start and not self.stop and not self.bit_cntrl:
            super(I2cAgent, self).setEnable(en)
        else:
            # wait until clock
            raise NotImplementedError()
