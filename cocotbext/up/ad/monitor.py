#******************************************************************************
# file:    monitor.py
#
# author:  JAY CONVERTINO
#
# date:    2025/03/11
#
# about:   Brief
# Monitor for uP
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

from cocotb.triggers import FallingEdge, RisingEdge, Event
from cocotb.result import TestFailure
from cocotb.binary import BinaryValue
from cocotb.queue import Queue

# Class: upMonitor
# Check signals to make sure they are applied properly.
class upMonitor(upBase):
  # Constructor: __init__
  # Setup defaults and call base class constructor.
  def __init__(self, entity, name, clock, resetn, *args, **kwargs):
    super().__init__(entity, name, clock, resetn, *args, **kwargs)

    self.log.info("uP Monitor")
    self.log.info("uP Monitor version %s", __version__)
    self.log.info("Copyright (c) 2025 Jay Convertino")
    self.log.info("https://github.com/johnathan-convertino-afrl/cocotbext-up")

  # Function: _check_type
  # Check and make sure we are only sending uptrans, this is only here to satisify the need to have it.
  def _check_type(self, trans):
      if(not isinstance(trans, apb3trans)):
          self.log.error(f'Transaction must be of type: {type(uptrans)}')
          return False

      return True

  # Method: _run_write
  # Coroutine for writing uP bus
  async def _run_write(self):
    while True:
      await RisingEdge(self.clock)

      if not self._resetn.value:
        assert self.bus.wreq.value == 0,  "RESET ISSUE: WREQ is not zero."
        self._idle.set()
        continue

      if self.bus.wack.value:
        if not self.bus.wreq.value:
          raise ValueError("WACK ISSUE: WACK is not zero when WREQ is zero.")

  # Method: _run_read
  # Coroutine for reading uP bus
  async def _run_read(self):
    while True:
      await RisingEdge(self.clock)

      if not self._resetn.value:
        assert self.bus.rreq.value == 0,  "RESET ISSUE: RREQ is not zero."
        self._idle.set()
        continue

      if self.bus.rack.value:
        if not self.bus.rreq.value:
          raise ValueError("RACK ISSUE: RACK is not zero when RREQ is zero.")



