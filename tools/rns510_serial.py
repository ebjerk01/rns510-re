#!/usr/bin/env python3
"""
rns510_serial.py — RNS-510 serial console client: read/write vehicle coding and
recover the theft-protection PIN, over the unit's VxWorks tShell.

Clean-room tool built from this project's own reverse-engineering (see FINDINGS.md
and 3810-analysis.md) — the VxWorks tShell at 115200 8N1 on the 26-pin connector,
and the coding command vocabulary (SetCoding / SetRegDataHex / ReadRegData /
TestCoding) plus the theft-PIN check (TpPvVerifyPin, range 0–1999).

  OWNERSHIP: PIN recovery requires a physical serial connection to the unit. Use it
  only to recover the login/SAFE code of a radio you own or are authorised to service.

  STATUS — IMPORTANT: the tShell command NAMES and the register map are from
  firmware RE, but the EXACT on-wire command invocation and the response strings are
  NOT yet confirmed on hardware (this project had no serial console attached). The
  command templates below are best-effort and MUST be verified/adjusted on a real
  unit before you trust them — especially the PIN-verify command and its
  success/failure patterns. Treat this as a documented protocol scaffold, not a
  turnkey tool. (SlashGordon/rns510-code-finder is a working, independent PIN brute
  forcer; this adds the coding side and documents the command vocabulary.)

Requires: pyserial  (pip install pyserial)

Usage:
  rns510_serial.py --port /dev/ttyUSB0 reg 0x21                # read a register
  rns510_serial.py --port COM3 coding                          # dump coding array 0x400
  rns510_serial.py --port /dev/ttyUSB0 setreg 0x0B3A 012C      # write (asks to confirm)
  rns510_serial.py --port /dev/ttyUSB0 raw 'help'              # send any tShell line
  rns510_serial.py --port /dev/ttyUSB0 find-pin                # recover the PIN (0–1999)
"""
from __future__ import annotations
import argparse
import re
import sys
import time

try:
    import serial  # pyserial
except ImportError:
    sys.exit("This tool needs pyserial:  pip install pyserial")

# --- Command templates (VERIFY ON YOUR UNIT — see STATUS note above) --------
# These mirror the documented tShell / coding-lib calls. {reg}/{hex}/{pin} are
# substituted. Adjust the exact spelling to match what your unit's shell accepts.
CMD_READ_REG   = "ReadRegData({reg})"
CMD_READ_CODE  = "TestCoding(0x400)"
CMD_SET_REGHEX = 'SetRegDataHex({reg},"{hex}",0x0,0x{width:X},0x1)'
# PIN verify: the theft-protection check. The real entry point is TpPvVerifyPin;
# how it is invoked from the shell and what it prints on success/failure must be
# confirmed on hardware. Parameterised so you can set the confirmed strings.
CMD_VERIFY_PIN = "TpPvVerifyPin({pin})"
PIN_OK_RE      = r"(?i)(pin\s*ok|valid|accepted|unlock|= *0\b)"
PIN_BAD_RE     = r"(?i)(invalid|wrong|fail|denied|= *-?1\b)"


class Console:
    def __init__(self, port: str, baud: int = 115200, timeout: float = 1.5):
        self.ser = serial.Serial(port, baud, timeout=timeout,
                                 bytesize=8, parity="N", stopbits=1)
        time.sleep(0.2)
        self.ser.reset_input_buffer()

    def send(self, line: str, settle: float = 0.25) -> str:
        self.ser.reset_input_buffer()
        self.ser.write((line + "\r\n").encode("latin-1", "replace"))
        self.ser.flush()
        time.sleep(settle)
        out = bytearray()
        deadline = time.time() + max(self.ser.timeout or 1.0, 1.0)
        while time.time() < deadline:
            chunk = self.ser.read(256)
            if chunk:
                out += chunk
                deadline = time.time() + 0.4   # extend while data flows
            else:
                break
        return out.decode("latin-1", "replace").strip()

    def close(self):
        try:
            self.ser.close()
        except Exception:
            pass


def cmd_reg(c: Console, reg: str):
    print(c.send(CMD_READ_REG.format(reg=reg)))


def cmd_coding(c: Console):
    print(c.send(CMD_READ_CODE))


def cmd_setreg(c: Console, reg: str, hexval: str, assume_yes: bool):
    width = max(1, (len(hexval) + 1) // 2)
    line = CMD_SET_REGHEX.format(reg=reg, hex=hexval, width=width)
    print(f"About to send: {line}")
    if not assume_yes:
        if input("Write this coding value? [y/N] ").strip().lower() != "y":
            print("aborted."); return
    print(c.send(line))


def cmd_raw(c: Console, line: str):
    print(c.send(line))


def cmd_find_pin(c: Console, start: int, stop: int, ok_re: str, bad_re: str,
                 delay: float, verify_cmd: str):
    ok = re.compile(ok_re); bad = re.compile(bad_re)
    print(f"Trying PINs {start}..{stop} with '{verify_cmd}'.")
    print("If this never matches, confirm the verify command + response strings "
          "on your unit and pass --ok-re/--bad-re/--verify-cmd.")
    for pin in range(start, stop + 1):
        resp = c.send(verify_cmd.format(pin=f"{pin:04d}"))
        tag = "?"
        if ok.search(resp):
            print(f"\nPIN FOUND: {pin:04d}\n  response: {resp!r}")
            return 0
        if bad.search(resp):
            tag = "bad"
        if pin % 50 == 0 or tag == "?":
            print(f"  {pin:04d}: {tag}" + (f"  {resp!r}" if tag == "?" else ""))
        time.sleep(delay)
    print("\nExhausted range without a match. Verify the command/response strings.")
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(description="RNS-510 serial coding / PIN tool")
    ap.add_argument("--port", required=True, help="serial port, e.g. /dev/ttyUSB0 or COM3")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--timeout", type=float, default=1.5)
    ap.add_argument("-y", "--yes", action="store_true", help="don't prompt before writes")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("coding", help="dump the 0x400 coding array")
    p = sub.add_parser("reg", help="read a register"); p.add_argument("reg")
    p = sub.add_parser("setreg", help="write a hex register value")
    p.add_argument("reg"); p.add_argument("hex")
    p = sub.add_parser("raw", help="send a raw tShell line"); p.add_argument("line")
    p = sub.add_parser("find-pin", help="recover the theft-protection PIN")
    p.add_argument("--start", type=int, default=0)
    p.add_argument("--stop", type=int, default=1999)
    p.add_argument("--delay", type=float, default=0.05)
    p.add_argument("--ok-re", default=PIN_OK_RE)
    p.add_argument("--bad-re", default=PIN_BAD_RE)
    p.add_argument("--verify-cmd", default=CMD_VERIFY_PIN,
                   help="override the PIN verify command template (use {pin})")
    a = ap.parse_args()

    try:
        c = Console(a.port, a.baud, a.timeout)
    except Exception as e:
        sys.exit(f"Could not open {a.port}: {e}")
    try:
        if a.cmd == "coding":
            cmd_coding(c); return 0
        if a.cmd == "reg":
            cmd_reg(c, a.reg); return 0
        if a.cmd == "setreg":
            cmd_setreg(c, a.reg, a.hex, a.yes); return 0
        if a.cmd == "raw":
            cmd_raw(c, a.line); return 0
        if a.cmd == "find-pin":
            return cmd_find_pin(c, a.start, a.stop, a.ok_re, a.bad_re, a.delay,
                                a.verify_cmd)
    finally:
        c.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
