#!/usr/bin/env python3
"""Communication check for the iCEBreaker's UART (FT2232H channel B).

Stdlib only (termios, no pyserial). Opens the port at 115200 8N1 and reports:
  1. whether anything arrives unprompted (banner / prompt),
  2. whether each of the 256 byte values is echoed back unchanged,
  3. how the echo behaves under a back-to-back burst.
Usage: python3 tools/uart-echo-check.py [/dev/cu.usbserial-XXXXXXX1] [baud]
"""
import glob, os, select, sys, termios, time

port = sys.argv[1] if len(sys.argv) > 1 else (sorted(glob.glob("/dev/cu.usbserial-*1")) or [None])[0]
baud = int(sys.argv[2]) if len(sys.argv) > 2 else 115200
if not port:
    sys.exit("no /dev/cu.usbserial-*1 — is the board plugged in?")

fd = os.open(port, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
a = termios.tcgetattr(fd)
a[0] = a[1] = a[3] = 0                              # raw: no input/output/local processing
a[2] = termios.CS8 | termios.CREAD | termios.CLOCAL  # 8N1, ignore modem lines
a[4] = a[5] = getattr(termios, "B%d" % baud)
termios.tcsetattr(fd, termios.TCSANOW, a)
termios.tcflush(fd, termios.TCIOFLUSH)

def read_for(seconds):
    got, t0 = b"", time.time()
    while time.time() - t0 < seconds:
        r, _, _ = select.select([fd], [], [], 0.05)
        if r:
            try: got += os.read(fd, 4096)
            except BlockingIOError: pass
    return got

print(f"port {port}, {baud} 8N1 — whole check takes ~35 s", flush=True)
idle = read_for(3.0)
print(f"1. idle 3 s: {len(idle)} bytes {idle[:40]!r}", flush=True)

print("2. sending 256 byte values one at a time, 100 ms each — about 26 s ...", flush=True)
missing, wrong = [], []
for v in range(256):
    os.write(fd, bytes([v]))
    b = read_for(0.1)
    if b == b"": missing.append(v)
    elif b != bytes([v]): wrong.append((v, b))
print(f"2. 256 values one at a time: {256 - len(missing) - len(wrong)} echoed exactly, "
      f"{len(missing)} missing {[hex(v) for v in missing][:8]}, {len(wrong)} altered {wrong[:4]}")

for n in (7, 64, 256):
    payload = bytes((i * 7 + 3) & 0xFF for i in range(n))
    os.write(fd, payload)
    back = read_for(1.0)
    print(f"3. burst of {n:>3} bytes back-to-back: {len(back):>3} returned, "
          f"{'exact' if back == payload else 'NOT exact'}")
os.close(fd)
