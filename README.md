# iCEBreaker V1.1a — board notes and the factory bitstream

A 1BitSquared **iCEBreaker V1.1a** FPGA board, received 2026-09-10. This repo
holds what was on it when it arrived and how it was identified, so nothing is
lost when the flash is first overwritten. It may be folded into a project repo
later.

## The board

| Item | Value | How known |
|---|---|---|
| FPGA | Lattice **iCE40UP5K**, SG48 (QFN48), 5,280 LCs, 128 kbit BRAM, 1 Mbit SPRAM | `iceunpack` reports `.device 5k`; vendor spec |
| Configuration flash | **Winbond W25Q128JV**, 16 MB, JEDEC ID `EF 40 18` | `iceprog -t` |
| USB bridge | FTDI **FT2232H**, VID `0x0403` PID `0x6010`, USB-C on V1.1a | `ioreg`: vendor "1BitSquared", product "iCEBreaker V1.1a", serial `ibxXrY9N` |
| Serial ports on macOS | `/dev/cu.usbserial-ibxXrY9N0` (channel A, SPI/flash for `iceprog`), `…N1` (channel B, UART) | same layout as the iCEstick |
| Clock | 12 MHz oscillator on pin 35 | official pcf |
| On the main board | LEDR_N 11, LEDG_N 37 (active-low), BTN_N 10, RGB LED 39/40/41 (active-low, mounted on V1.1a), 64 Mbit QSPI PSRAM (V1.1a), CRESET button (V1.1a) | official pcf, vendor docs |
| Snap-off strip (Pmod 2) | 5 LEDs: LED1 26, LED2 27, LED3 25, LED4 23, LED5 21 (active-high); 3 buttons: BTN1 20, BTN2 19, BTN3 18 | official pcf, `docs/reference/icebreaker.pcf` |
| Pmod 1A / 1B | P1A1–4, 7–10 = 4, 2, 47, 45, 3, 48, 46, 44; P1B1–4, 7–10 = 43, 38, 34, 31, 42, 36, 32, 28 | official pcf |

Toolchain used here: `iceprog`/`iceunpack`/`icebox_vlog` from Homebrew `icestorm 1.1`,
on the M2 Mac mini (macOS 26.6.2). Same tools as `agentic-loop-riscv`.

## First power-on, 2026-09-10 18:22

Plugged into the M2. The two serial ports appeared; the five LEDs on the snap-off
strip came alive at once, which also proves the strip's tab traces are intact.
The board's own link test, run before anything else:

```
$ iceprog -t
init..
cdone: high          <- the FPGA had already configured itself from flash
reset..
cdone: low
flash ID: 0xEF 0x40 0x18 0x00
cdone: high          <- reconfigured from flash again after the reset
Bye.
```

What that sequence means: at power-on the FT2232H enumerates, the FPGA leaves
reset, reads the bitstream at flash address 0 as SPI master, and raises CDONE.
The CDONE LED on the board lights at that moment. `iceprog -t` holds the FPGA
in reset while it talks to the flash, then releases it, so the demo restarts.

## The factory bitstream — read out, not modified

Read on 2026-09-10 18:32 with `iceprog -R 1M factory/flash-1M.bin`. That is a
read of the first 1 MB of the flash; nothing was written. Files:

| File | Bytes | SHA-256 | What |
|---|---|---|---|
| `factory/flash-1M.bin` | 1,048,576 | `a49bdd80…f3a7e8` | raw first 1 MB of flash. Everything after the bitstream is `0xFF` (erased) |
| `factory/factory-bitstream.bin` | 104,090 | `abe7f245…69b7c1` | the bitstream alone: bytes 0 to the first 256-byte run of `0xFF`. Ends with the iCE40 wake-up command `01 06` |
| `factory/factory-bitstream.asc` | 735,239 | | `iceunpack` output: the textual IceStorm bitstream, `.device 5k`, empty `.comment` |
| `factory/factory-netlist.v` | 164,119 | | `icebox_vlog -p /dev/null` output: a gate-level Verilog netlist of LUTs and flip-flops, ports named by I/O tile |

Full hashes are in `factory/SHA256SUMS`. To put the factory state back exactly:

```
iceprog factory/factory-bitstream.bin        # writes flash from address 0 — this is the only write in this repo's instructions
```

The header is `FF 00 00 FF 7E AA 99 7E` with an empty comment field, which is
what `icepack` from IceStorm produces; a Lattice Radiant bitstream would carry
a version string there. So the factory design was built with the open-source flow.

### What the design is, from the netlist

The recovered netlist (`factory/factory-netlist.v`) has 30 I/O ports, 141
registers and 285 assignments, all on one global clock from pin 35. Mapped to
the package with `icebox.pinloc_db["5k-sg48"]`:

| Direction | Package pins | Board function |
|---|---|---|
| input | 35 | 12 MHz clock |
| input | 10 | main-board button |
| input | 20, 19, 18 | the three strip buttons |
| input | 6 | UART RX from the FT2232H |
| output | 9 | UART TX to the FT2232H |
| output | 11, 37 | red and green main-board LEDs |
| output | 26, 27, 25, 23, 21 | the five strip LEDs LED1–LED5 |
| output | 4, 2, 47, 45, 3, 48, 46, 44 | all eight Pmod 1A pins (P1A1–4, 7–10) |
| output | 43, 38, 34, 31, 42, 36, 32, 28 | all eight Pmod 1B pins (P1B1–4, 7–10) |

Every output is driven directly from a flip-flop, and every Pmod pin is driven.
That shape — drive everything, read every button, talk on the UART — is a
production test design, not an LED demo written for the buyer: 1BitSquared
programs each board with something a test fixture can exercise, and the LED
pattern you see is that design running with nothing attached. The RGB LED pins
(39, 40, 41) and the PSRAM are not used by it.

What the LED pattern and the UART actually do has **not** been worked out from
the LUT equations. The netlist is small enough that it could be.

All pin names come from the official `icebreaker.pcf`, kept in
`docs/reference/`. The mapping was checked against it line by line.

## The UART: the factory design is an echo at 115200 8N1

Probed 2026-09-10 on channel B (`/dev/cu.usbserial-ibxXrY9N1`) with a plain
`termios` script, no pyserial. Findings:

- **Silent when idle.** 5 s at 115200 with nothing sent: 0 bytes. It does not
  print a banner or a prompt.
- **Echoes every byte at 115200 8N1.** All 256 byte values sent one at a time,
  150 ms apart: every one came back unchanged. `hello\r\n` came back as
  `hello\r\n`. At 9600 the reply is garbage, so the rate is fixed at 115200.
- **No buffering.** 256 bytes back-to-back returned 233; a 2,000-byte burst
  returned 932. Pairs of bytes survive, longer streams lose characters. The
  echo path in the netlist is RX pin 6 → flip-flops → TX pin 9 with no FIFO,
  which fits a test-fixture loopback exactly.

So yes, the board talks: whatever you type comes straight back, byte for byte,
as long as you do not stream. That is a UART link test, not a console. Anything
more useful needs a design of your own on the FPGA.

```
$ picocom -b 115200 /dev/cu.usbserial-ibxXrY9N1     # type; each key echoes. Ctrl-A Ctrl-X to quit
```

### The communication check, reproducible

`tools/uart-echo-check.py` is the probe, stdlib only. It opens channel B raw at
115200 8N1, listens for a banner, sends every byte value on its own, then three
bursts. Run on 2026-09-10 18:49:

```
$ python3 tools/uart-echo-check.py
port /dev/cu.usbserial-ibxXrY9N1, 115200 8N1 — whole check takes ~35 s
1. idle 3 s: 0 bytes b''
2. sending 256 byte values one at a time, 100 ms each — about 26 s ...
2. 256 values one at a time: 256 echoed exactly, 0 missing [], 0 altered []
3. burst behaviour (informational — the factory echo has no buffer, so long bursts lose bytes):
   burst of   7 bytes back-to-back:   7 returned
   burst of  64 bytes back-to-back:  59 returned, 5 lost
   burst of 256 bytes back-to-back: 233 returned, 23 lost

PASS — the board echoes every byte; USB, FTDI channel B and the FPGA's UART pins all work.
       Lost bytes in the 64/256 bursts are the factory design's unbuffered echo, not a link fault.
```

The verdict is step 2 plus the 7-byte burst: every byte value comes back
unchanged, so the whole path works — USB, the FT2232H's channel B, the FPGA's
RX and TX pins, and the design in flash. The script exits 0 on PASS, 1 on FAIL.

Step 3 is not a test, it is a description of the factory design. Its echo holds
one byte and cannot take the next one in while it is still sending the previous
one out, so a stream loses roughly one byte in eleven. That is a property of
the design that happened to be in the flash, not of the board: your own design
with a small FIFO will not lose any. The script takes an optional port and baud
(`tools/uart-echo-check.py /dev/cu.usbserial-XXXXXXX1 115200`) and tests the
factory echo specifically — once a different design is on the FPGA, expect FAIL.

## Links

Board and vendor:

- Product page (V1.1a changes listed): https://1bitsquared.com/products/icebreaker
- Hardware design files, schematics for every revision: https://codeberg.org/icebreaker-fpga/icebreaker
- Verilog examples and the official `icebreaker.pcf`: https://codeberg.org/icebreaker-fpga/icebreaker-verilog-examples
- Documentation site: https://docs.icebreaker-fpga.org/ — board page: https://docs.icebreaker-fpga.org/hardware/icebreaker/
- Crowd Supply campaign page (history, specs): https://www.crowdsupply.com/1bitsquared/icebreaker-fpga
- Original GitHub org (archived, redirects to Codeberg): https://github.com/icebreaker-fpga

Chips:

- Lattice iCE40 UltraPlus family data sheet (FPGA-DS-02008): https://www.latticesemi.com/view_document?document_id=51968
- Lattice iCE40 Programming and Configuration (FPGA-TN-02001, ex-TN1248): https://www.latticesemi.com/view_document?document_id=46502
- Lattice iCE40 UltraPlus product page: https://www.latticesemi.com/Products/FPGAandCPLD/iCE40UltraPlus
- Winbond W25Q128JV data sheet: https://www.winbond.com/resource-files/W25Q128JV%20RevH%2003102021%20Plus.pdf
- FTDI FT2232H data sheet: https://ftdichip.com/wp-content/uploads/2024/09/DS_FT2232H.pdf

Tools:

- Project IceStorm (iceprog, icepack/iceunpack, icebox): https://github.com/YosysHQ/icestorm
- IceStorm bitstream format notes: https://bygone.clairexen.net/icestorm/format.html
- nextpnr (`--up5k --package sg48` for this board): https://github.com/YosysHQ/nextpnr
- Yosys: https://github.com/YosysHQ/yosys
- learn-fpga's iCEBreaker tutorial (FemtoRV on this board): https://github.com/BrunoLevy/learn-fpga/blob/master/FemtoRV/TUTORIALS/IceBreaker.md

Local copies of the schematics, datasheets, the pcf and the docs pages are in
[`docs/`](docs/README.md).
