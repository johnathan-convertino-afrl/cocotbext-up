#******************************************************************************
# file:    busbase.py
#
# author:  JAY CONVERTINO
#
# date:    2025/03/11
#
# about:   Brief
# classic bus define for packages
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

import logging

from typing import Iterable, Tuple, Any, Optional, Callable

import cocotb
from cocotb.queue import Queue
from cocotb.binary import BinaryValue
from cocotb.triggers import FallingEdge, Timer, First, Event, Edge
from cocotb.handle import SimHandleBase
from cocotb_bus.bus import Bus

from abc import ABC

from .version import __version__

# Class: transaction
# Abstract class for transaction types
class transaction(ABC):
    pass

# Class: noSignal
# Class to use when a signal does not exist
class noSignal:
    def __init__(self, value = True):
        self.value = value

# Class: busbase
# A busbase to transmit test routine.
class busbase:
    _signals = []
    _optional_signals = []
    # Constructor: __init__
    # Initialize the object
    def __init__(self, entity: SimHandleBase, name: Optional[str], clock: SimHandleBase, *args: Any, **kwargs: Any):
        index = kwargs.get("array_idx", None)

        self.log = logging.getLogger("cocotb.%s.%s" % (entity._name, name))
        self.entity = entity
        self.clock = clock
        self.bus = Bus(
            self.entity, name, self._signals, optional_signals=self._optional_signals,
            **kwargs
        )

        # Give this instance a unique name
        self.name = name if index is None else "%s_%d" % (name, index)

        self.log.info(f'BUS base class for prefix {self.name}')

        super().__init__(*args, **kwargs)

        self.active = False

        # Variable: wqueue
        # Queue to store write requests
        self.wqueue = Queue()
        # Variable: qqueue
        # Queue to store read requests
        self.qqueue = Queue()
        # Variable: rqueue
        # Queue to store result of read requests
        self.rqueue = Queue()

        # Variable: _idle_read
        # Event trigger for cocotb read
        self._idle_read = Event()
        self._idle_read.clear()

        # Variable: _idle_write
        # Event trigger for cocotb write
        self._idle_write = Event()
        self._idle_write.clear()

        # Variable: self._run_cr
        # Thread instance of _run method
        self._run_cr = None
        self._restart()

    # Function: _restart
    # kill and restart _run thread.
    def _restart(self):
        if self._run_cr is not None:
            self._run_cr.kill()
            self.read_clear()
            self.write_clear()
        self._run_cr = cocotb.start_soon(self._run())

    # Function: write_count
    # How many items in the write queue
    def write_count(self):
        return self.wqueue.qsize()

    # Function: read_count
    # How many items in the read queue
    def read_count(self):
        return self.rqueue.qsize()

    # Function: write_empty
    # Is the quene empty?
    def write_empty(self):
        return self.wqueue.empty()

    # Function: read_empty
    # Is the quene empty?self.bus.penable.value
    def read_empty(self):
        return self.rqueue.empty()

    # Function: write_clear
    # Remove all write items from queue
    def write_clear(self):
        while not self.wqueue.empty():
            frame = self.wqueue.get_nowait()

    # Function: read_clear
    # Remove all read items from queue
    def read_clear(self):
        while not self.qqueue.empty():
            frame = self.qqueue.get_nowait()

        while not self.rqueue.empty():
            frame = self.rqueue.get_nowait()

    # Function: wait_read
    # Wait for the run thread to become idle from a read.
    async def wait_read(self):
        await self._idle_read.wait()

    # Function: wait_write
    # Wait for the run thread to become idle from a write.
    async def wait_write(self):
        await self._idle_write.wait()

    # Function: idle
    # Are all the queues empty and the _run is not active processing data.
    def idle(self):
        return self.write_empty() and self.read_empty() and not self.active

    # Function: write_trans
    # Write transaction to send to write queue
    async def write_trans(self, trans : transaction):
        if(isinstance(trans, list)):
            for t in trans:
                await self._write(t)
        else:
            await self._write(trans)

    # Function: read_trans
    # Read bus and output and tranaction.
    async def read_trans(self, trans : transaction):
        if(isinstance(trans, list)):
            temp = []
            for t in trans:
                await self._queue_read(t)
            for t in trans:
                temp.append(await self._read(t))
            return temp
        else:
            await self._queue_read(trans)
            return await self._read(trans)


    # Function: _write
    # Write data one element at a time
    async def _write(self, trans : transaction):
        if(self._check_type(trans)):
            await self.wqueue.put(trans)
            await self._idle_write.wait()
            self._idle_write.clear()

    # Function: _queue_read
    # Setup queue for read requests
    async def _queue_read(self, trans : transaction):
        if(self._check_type(trans)):
            await self.qqueue.put(trans)

    # Function: _read
    # Read dat one element at a time
    async def _read(self, trans : transaction):
        if(self._check_type(trans)):
            while self.read_empty():
                self._idle_read.clear()
                await self._idle_read.wait()
            return await self.rqueue.get()

    # Function: _check_type
    # Check and make sure we are only sending the correct transaction type
    def _check_type(self, trans):
        raise NotImplementedError("Sub-classes of busbase should define a "
                                  "_check_type method")

    # Method: _run
    # Virtual method for _run thread that deals with read and write queues.
    async def _run(self):
        raise NotImplementedError("Sub-classes of busbase should define a "
                                  "_run method")
