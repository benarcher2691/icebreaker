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
| On the main board | 2 LEDs (red pin 11, green pin 37, active-low), 1 button (pin 10), RGB LED (39/40/41, mounted on V1.1a), 64 Mbit QSPI PSRAM (V1.1a), CRESET button (V1.1a) | vendor docs |
| Snap-off strip (Pmod 2) | 5 LEDs (pins 27, 21, 25, 23, 26 = D1…D5, active-high) and 3 buttons (20, 19, 18) | official pcf |
| Pmod 1A / 1B | 8 + 8 I/O: 4, 2, 47, 45, 3, 48, 46, 44 / 43, 38, 34, 31, 42, 36, 32, 28 | vendor pinout |

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
| output | 27, 21, 25, 23, 26 | the five strip LEDs D1–D5 |
| output | 4, 2, 47, 45, 3, 48, 46, 44 | all eight Pmod 1A pins |
| output | 43, 38, 34, 31, 42, 36, 32, 28 | all eight Pmod 1B pins |

Every output is driven directly from a flip-flop, and every Pmod pin is driven.
That shape — drive everything, read every button, talk on the UART — is a
production test design, not an LED demo written for the buyer: 1BitSquared
programs each board with something a test fixture can exercise, and the LED
pattern you see is that design running with nothing attached. The RGB LED pins
(39, 40, 41) and the PSRAM are not used by it.

What the LED pattern and the UART actually do has **not** been worked out from
the LUT equations. The netlist is small enough that it could be.

Pin names for the strip and UART come from the official `icebreaker.pcf`
(via the learn-fpga copy); Pmod 1 and the RGB pins from the vendor pinout.

## Sources

- Hardware repo (Codeberg): https://codeberg.org/icebreaker-fpga/icebreaker
- Docs: https://docs.icebreaker-fpga.org/hardware/icebreaker/
- Product page with the V1.1a change list: https://1bitsquared.com/products/icebreaker
- IceStorm (iceprog, iceunpack, icebox): https://github.com/YosysHQ/icestorm
