#******************************************************************************
# file:    absbus.py
#
# author:  JAY CONVERTINO
#
# date:    2025/03/26
#
# about:   Brief
# abstraction of the Analog Devices uP bus
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

import cocotb

from cocotb.triggers import Timer, RisingEdge

from cocotbext.busbase import *

import enum

# Class: uptrans
# create an object that associates a data member and address for operation.
class uptrans(transaction):
    def __init__(self, address, data=None):
        self.address = address
        self.data = data

# Class: upState
# An enum class that provides the current state and will change states per spec.
class upState(enum.IntEnum):
  IDLE = 1
  REQ  = 2
  ERROR = 99

# Class: upBase
# abstract base class that defines uP signals
class upBase(busbase):
  # Variable: _signals
  # List of signals that are required
  _signals = ["wreq", "wack", "waddr", "wdata", "rreq", "rack", "raddr", "rdata"]

  # Constructor: __init__
  # Setup defaults and call base class constructor.
  def __init__(self, entity, name, clock, resetn, *args, **kwargs):

    super().__init__(entity, name, clock, *args, **kwargs)

    self._writeState = upState.IDLE

    self._readState = upState.IDLE

    self._resetn = resetn

    self._run_read_cr = None

    self._run_write_cr = None

  # Function: _restart_rw
  # kill and restart _run thread.
  def _restart_rw(self):
      if self._run_read_cr is not None:
          self._run_read_cr.kill()
          self.read_clear()
      self._run_read_cr = cocotb.start_soon(self._run_read())

      if self._run_write_cr is not None:
          self._run_write_cr.kill()
          self.write_clear()
      self._run_write_cr = cocotb.start_soon(self._run_write())

  # Method: _run
  # _run thread that deals with read and write.
  async def _run(self):
    self.active = False
    self._restart_rw()

    while True:

      await RisingEdge(self.clock)

      if self._writeState != upState.IDLE or self._readState != upState.IDLE:
        self.active = True
      else:
        self.active = False

  # Method: _run_read
  # Abstract method for read thread
  async def _run_read(self):
    raise NotImplementedError("Sub-classes of absbus should define a "
                                  "_run_read method")

  # Method: _run_write
  # Abstract method for write thread
  async def _run_write(self):
    raise NotImplementedError("Sub-classes of absbus should define a "
                                  "_run_write method")
