#******************************************************************************
# file:    driver.py
#
# author:  JAY CONVERTINO
#
# date:    2025/03/11
#
# about:   Brief
# Bus Driver for Analog Devices uP
#
# license: License MIT
# Copyright 2025 Jay Convertino
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
#
#******************************************************************************

from ..version import __version__
from .absbus import *

from cocotb.triggers import FallingEdge, Edge, RisingEdge, Event
from cocotb.result import TestFailure
from cocotb.binary import BinaryValue
from cocotb.queue import Queue

# Class: upMaster
# Drive slave devices over the uP bus
class upMaster(upBase):
  # Constructor: __init__
  # Setup defaults and call base class constructor.
  def __init__(self, entity, name, clock, resetn, *args, **kwargs):
    super().__init__(entity, name, clock, resetn, *args, **kwargs)

    self.log.info("uP Master")
    self.log.info("uP Master version %s", __version__)
    self.log.info("Copyright (c) 2025 Jay Convertino")
    self.log.info("https://github.com/johnathan-convertino-afrl/cocotbext-up")

    # setup bus to default value imediatly
    self.bus.wreq.setimmediatevalue(0)
    self.bus.waddr.setimmediatevalue(0)
    self.bus.wdata.setimmediatevalue(0)
    self.bus.rreq.setimmediatevalue(0)
    self.bus.raddr.setimmediatevalue(0)

  # Function: read
  # Read from a address and return data
  async def read(self, address):
    trans = None
    if(isinstance(address, list)):
      temp = []
      for a in address:
        temp.append(uptrans(a))
      temp = await self.read_trans(temp)
      #need a return with the data list only. This is only a guess at this point
      return [temp[i].data for i in range(len(temp))]
    else:
      trans = await self.read_trans(uptrans(address))
      return trans.data

  # Function: write
  # Write to a address some data
  async def write(self, address, data):
    if(isinstance(address, list) or isinstance(data, list)):
      if(len(address) != len(data)):
        self.log.error(f'Address and data vector must be the same length')
      temp = []
      for i in range(len(address)):
        temp.append(uptrans(address[i], data[i]))
      await self.write_trans(temp)
    else:
      await self.write_trans(uptrans(address, data))

  # Function: _check_type
  # Check and make sure we are only sending 2 bytes at a time and that it is a bytes/bytearray
  def _check_type(self, trans):
      if(not isinstance(trans, uptrans)):
          self.log.error(f'Transaction must be of type: {type(uptrans)}')
          return False

      return True

  # Method: _run_write
  # method for write thread
  async def _run_write(self):
    prevState = self._upWriteStateMachine

    while True:
      await RisingEdge(self.clock)

      if(self._upWriteStateMachine == upState.IDLE):
        if not self.wqueue.empty():
          trans = await self.wqueue.get()
          self.bus.wreq.value = 1
          self.bus.waddr.value = trans.address
          self.bus.wdata.value = trans.data
          self._upWriteStateMachine = upState.REQ
        else:
          self._idle_write.set()

          self.bus.wreq.value = 0
          self.bus.waddr.value = 0
          self.bus.wdata.value = 0
      elif(self._upWriteStateMachine == upState.REQ):
        if(self.wqueue.empty() and self.bus.wack.value):
          self.bus.wreq.value = 0
          self.bus.waddr.value = 0
          self.bus.wdata.value = 0
          self._upWriteStateMachine = upState.IDLE
          self._idle_write.set()
        elif(self.bus.wack.value):
          trans = await self.wqueue.get()
          self.bus.waddr.value = trans.address
          self.bus.wdata.value = trans.data
          self._upWriteStateMachine = upState.ACK
      elif(self._upWriteStateMachine == upState.ACK):
        if(self.wqueue.empty() and self.bus.wack.value):
          self.bus.wreq.value = 0
          self.bus.waddr.value = 0
          self.bus.wdata.value = 0
          self._upWriteStateMachine = upState.IDLE
          self._idle_write.set()
        elif(self.bus.wack.value):
          trans = await self.wqueue.get()
          self.bus.waddr.value = trans.address
          self.bus.wdata.value = trans.data

      if(self._upWriteStateMachine != prevState):
        self.log.info(f'uP MASTER STATE: {self._upWriteStateMachine.name} : BUS WRITE')

      prevState = self._upWriteStateMachine

  # Method: _run_read
  # method for read thread
  async def _run_read(self):
    prevState = self._upReadStateMachine

    trans = None

    while True:

      await RisingEdge(self.clock)

      if(self._upReadStateMachine == upState.IDLE):
        if not self.qqueue.empty():
          trans = await self.qqueue.get()
          self.bus.rreq.value = 1
          self.bus.raddr.value = trans.address
          self._upReadStateMachine = upState.REQ
        else:
          self._idle_read.set()
          self.bus.rreq.value = 0
          self.bus.raddr.value = 0
      elif(self._upReadStateMachine == upState.REQ):
        if(self.qqueue.empty() and self.bus.rack.value):
          trans.data = self.bus.rdata.value
          await self.rqueue.put(trans)
          self.bus.rreq.value = 0
          self.bus.raddr.value = 0
          self._upReadStateMachine = upState.IDLE
          self._idle_read.set()
          self.log.info(f'_idle set 2 {trans.data}')
        elif(self.bus.rack.value):
          trans.data = self.bus.rdata.value
          await self.rqueue.put(trans)
          trans = await self.qqueue.get()
          self._upReadStateMachine = upState.ACK
      elif(self._upReadStateMachine == upState.ACK):
        if(self.qqueue.empty() and self.bus.rack.value):
          trans.data = self.bus.rdata.value
          await self.rqueue.put(trans)
          self.bus.rreq.value = 0
          self.bus.raddr.value = 0
          self._upReadStateMachine = upState.IDLE
          self._idle_read.set()
          self.log.info(f'_idle set 3')
        elif(self.bus.rack.value):
          trans.data = self.bus.rdata.value
          await self.rqueue.put(trans)
          trans = await self.qqueue.get()

      if(self._upReadStateMachine != prevState):
        self.log.info(f'uP MASTER STATE: {self._upReadStateMachine.name} : BUS READ')

      prevState = self._upReadStateMachine

# Class: upEchoSlave
# Respond to master reads and write by returning data, simple echo core.
class upEchoSlave(upBase):
  # Constructor: __init__
  # Setup defaults and call base class constructor.
  def __init__(self, entity, name, clock, resetn, numreg=256, *args, **kwargs):
    super().__init__(entity, name, clock, resetn, *args, **kwargs)

    self.log.info("uP Slave")
    self.log.info("uP Slave version %s", __version__)
    self.log.info("Copyright (c) 2025 Jay Convertino")
    self.log.info("https://github.com/johnathan-convertino-afrl/cocotbext-apb")

    self.bus.rack.setimmediatevalue(0)
    self.bus.rdata.setimmediatevalue(0)
    self.bus.wack.setimmediatevalue(0)

    self._registers = {}

    for i in range(numreg):
      self._registers[i] = 0

  # Function: _check_type
  # Check and make sure we are only sending a type of uptrans.
  def _check_type(self, trans):
      if(not isinstance(trans, uptrans)):
          self.log.error(f'Transaction must be of type: {type(uptrans)}')
          return False

      return True

  # Method: _run_write
  # method for write thread
  async def _run_write(self):
    while True:
      await Edge(self.bus.wreq)
      self.bus.wack.setimmediatevalue(self.bus.wack.value == self.bus.wreq.value)

      await RisingEdge(self.clock)

      if(self.bus.wreq.value):
        self.log.info(f'uP SLAVE: REGISTER WRITE')
        self.bus.wack.value = 1
        self._registers[self.bus.waddr.value.integer] = self.bus.wdata.value.integer
        self._upWriteStateMachine = upState.ACK
      else:
        self.bus.wack.value = 0
        self._idle_write.set()
        self._upReadStateMachine = upState.IDLE


  # Method: _run_read
  # method for read thread
  async def _run_read(self):
    while True:
      await Edge(self.bus.rreq)
      self.bus.rack.setimmediatevalue(self.bus.rack.value == self.bus.rreq.value)

      await RisingEdge(self.clock)

      if(self.bus.rreq.value):
        self.log.info(f'uP SLAVE: REGISTER READ')
        self.bus.rack.value = 1
        self.bus.rdata.value = self._registers[self.bus.raddr.value.integer]
        self._upReadStateMachine = upState.ACK
      else:
        self.bus.rack.value = 0
        self._idle_read.set()
        self._upReadStateMachine = upState.IDLE
