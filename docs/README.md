# docs/ — downloaded reference material for the iCEBreaker V1.1a

Everything here is a copy of a public document, kept so the repo stays useful
if a link dies. Each file has its origin next to it (`*.url`, `*.SOURCE`, or a
comment at the top). Fetched 2026-09-10 on the M2 unless stated otherwise.

## board/ — from the hardware repo, `codeberg.org/icebreaker-fpga/icebreaker`

Commit in `board/SOURCE-commit.txt`. The hardware is open source (see the
repo README for its licence).

| File | What |
|---|---|
| `icebreaker-v1.1a-schematic.pdf` | **This board's schematic.** V1.1a: USB-C, RGB LED and PSRAM mounted, CRESET button, length-matched Pmods |
| `icebreaker-v1.0e-schematic.pdf` | Previous revision, the last one with full PCB files in the repo; same pinout |
| `icebreaker-v1.0b-pinout-legend.jpg` | Pinout legend photo (V1.0b, pinout unchanged since) |
| `icebreaker-v1.0b-pinout-legend-jumpers.jpg` | Same, with the jumper options marked |
| `icebreaker-block-diagram.jpg` | Block diagram |
| `icebreaker-hardware-repo-README.md` | The hardware repo's README: feature list, revision history, the snap-off strip |

## datasheets/ — the three chips that matter, plus the configuration tech note

| File | Document | Why |
|---|---|---|
| `iCE40-UltraPlus-Family-Data-Sheet-FPGA-DS-02008-2.4.pdf` | Lattice iCE40 UltraPlus family data sheet, v2.4 (Feb 2025) | the UP5K: I/O banks, SPRAM, PLL, DSP, timing, pinout |
| `iCE40-Programming-and-Configuration-FPGA-TN-02001.pdf` | Lattice technical note FPGA-TN-02001 v3.5 (formerly TN1248) | **what happens at power-on:** CRESET/CDONE, SPI master boot from flash, bitstream layout, multi-boot |
| `W25Q128JV-datasheet.pdf` | Winbond W25Q128JV serial flash, rev H (Mar 2021) | the 16 MB configuration flash; JEDEC ID `EF 40 18` as read by `iceprog -t` |
| `FT2232H-datasheet.pdf` | FTDI FT2232H, v2.21 | the USB bridge: channel A drives the flash/FPGA for `iceprog`, channel B is the UART |

Lattice's direct `-/media/…` links return 404 to non-browser clients; the
`view_document?document_id=…` endpoint works (see the `.url` files). FTDI's own
site blocks downloads; the copy is from a university mirror and is the genuine
v2.21 document.

## reference/ — small files used directly by tools

| File | What |
|---|---|
| `icebreaker.pcf` | **The official pin constraint file** (50 `set_io` lines) from `codeberg.org/icebreaker-fpga/icebreaker-verilog-examples`, commit in `icebreaker.pcf.SOURCE`. This is what the pin names in the top-level README come from |

## web/ — docs.icebreaker-fpga.org, converted to Markdown with pandoc

`docs.icebreaker-fpga.org-index.md`, `-getting-started.md`, `-hardware-icebreaker.md`.
Thin pages; the source URL is in the first line of each.

## Not captured

- Project IceStorm's bitstream-format write-up (`bygone.clairexen.net/icestorm/format.html`)
  — the mirror's TLS certificate no longer matches and the page is not in the
  IceStorm repo. The header bytes and the wake-up command are also described in
  FPGA-TN-02001 above.
