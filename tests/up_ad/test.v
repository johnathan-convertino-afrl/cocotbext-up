//******************************************************************************
// file:    test.v
//
// author:  JAY CONVERTINO
//
// date:    2025/03/17
//
// about:   Brief
// Test bench for analog devices uP using cocotb
//
// license: License MIT
// Copyright 2025 Jay Convertino
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to
// deal in the Software without restriction, including without limitation the
// rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
// sell copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in
// all copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
// FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
// IN THE SOFTWARE.
//
//******************************************************************************

`timescale 1ns/100ps

/*
 * Module: test
 *
 * Test bench loop for up
 *
 * Parameters:
 *
 *   ADDRESS_WIDTH   - Width of the uP address port, max 32 bit.
 *   BUS_WIDTH       - Width of the uP bus data port.
 *
 * Ports:
 *
 *   clk            - Clock for all devices in the core
 *   rstn           - Negative reset
 *   up_rreq        - uP bus read request
 *   up_rack        - uP bus read ack
 *   up_raddr       - uP bus read address
 *   up_rdata       - uP bus read data
 *   up_wreq        - uP bus write request
 *   up_wack        - uP bus write ack
 *   up_waddr       - uP bus write address
 *   up_wdata       - uP bus write data
 */
module test #(
    parameter ADDRESS_WIDTH = 32,
    parameter BUS_WIDTH = 4
  )
  (
    input                       clk,
    input                       rstn,
    inout                                     up_rreq,
    inout                                     up_rack,
    inout [ADDRESS_WIDTH-(BUS_WIDTH/2)-1:0]   up_raddr,
    inout [(BUS_WIDTH*8)-1:0]                 up_rdata,
    inout                                     up_wreq,
    inout                                     up_wack,
    inout [ADDRESS_WIDTH-(BUS_WIDTH/2)-1:0]   up_waddr,
    inout [(BUS_WIDTH*8)-1:0]                 up_wdata
  );

  //copy pasta, fst generation
  initial
  begin
    $dumpfile("test.fst");
    $dumpvars(0,test);
  end

endmodule
