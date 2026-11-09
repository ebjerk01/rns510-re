# SetConfig — analysis of a third-party RNS-510 coding tool

This documents **what a widely-circulated commercial RNS-510 coding/config tool
("SetConfig") is and how it works**, as determined by static analysis. It is here
for interoperability and research: to show that the unit can be coded with knowledge
we already have, without the paid tool.

> **Not included here:** the SetConfig binaries, its installer, its licence/key
> files, or any licence-bypass steps. This repo distributes none of that. The notes
> below describe behaviour observed by reverse-engineering; they are not a crack and
> deliberately omit the bypass values.

## What it is

A Windows GUI tool for reading and writing RNS-510 **coding** and for generating
flash/coding discs. The package contains:

- `SetConfig.exe` — the GUI (native PE32, x86).
- `LCode.exe` — a separate **Long/Short Coding decoder** (see below).
- A complete **SWL boot-disc skeleton** (`SwlFiles/`) plus **`mkisofs.exe`** — so the
  tool can build a Continental SWL boot-CD ISO to apply coding/flash.
- **VCDS-style coding label files** per part number (e.g. a `1T0-035-680.lbl` for the
  1T0 radios), authored in the familiar Ross-Tech label format.
- VW/Skoda/Seat splash bitmaps and USB cable drivers.

## How it works

1. **It is a GUI over the RNS-510 serial coding console.** `SetConfig.exe` links the
   FTDI `ftd2xx.dll` and talks to the unit over an **FTDI USB-serial** link. The
   coding operations are the same tShell/diagnostic console commands already
   documented from the firmware — `SetCoding(0x400, …)`, `SetRegDataHex(…)`,
   `ld < /tffs0/lib/diag/CodingTest.out`. In other words it drives the exact
   interface described in `FINDINGS.md`.

   **Interoperability takeaway:** you do not need this tool to code the unit. The
   same coding is reachable over the serial console (115200 8N1 on the service UART)
   with the commands in `FINDINGS.md`, using any USB-serial adapter.

2. **It also generates SWL discs the community way.** The bundled `SwlFiles/` holds
   a genuine Continental `BlScript.cfg`, `Version.txt` and `SWL.FLI`, and it shells
   out to `mkisofs.exe`. Its `Version.txt` is an authentic Continental header
   ("Software Loading CD for CP2 based units", CdTreeBuilder 3.06, ~3980-era build),
   covering 1T0035680D/F/G part numbers. This independently confirms the
   boot-CD-generation approach in `SD-FLASH-FEASIBILITY.md`: a tiny SWL boot CD
   + a generated DLSCRIPT is exactly how coding/flash discs are made.

3. **LCode.exe is a coding *decoder*, not a security tool.** It takes the unit's
   **Long Coding** or a 3/5/7/9-byte **Short Coding** string and decodes each
   byte/bit into human-readable meaning, driven by the VCDS label files, with
   hex↔decimal helpers. "LCode" = Long Code. It performs **no** login/SAFE-code or
   theft-protection calculation — there is no security bypass in it.

## Licensing (observed, high level)

SetConfig is gated on a **specific FTDI USB cable**: on start it checks for an FTDI
device whose EEPROM identity matches what it expects, and refuses a generic cable
("cable not compatible"). This is an ordinary FTDI-dongle scheme — the licence is
tied to the cable's EEPROM descriptor, not to the PC. The exact descriptor values
and the bypass are intentionally **not** reproduced here.

## How to replicate this analysis

All with free tools, on a copy of the package you already have — no running of the
tool required:

1. **Unpack the nested archives** to reach `SetConfig.msi`.
2. **Extract the MSI payload** with `msiextract` (from `msitools`):
   `msiextract SetConfig.msi`. (Generic `7z` can mishandle these; `msiextract`
   yields the real `SetConfig.exe`, `LCode.exe`, `SwlFiles/`, `Labels/`, etc.)
3. **Identify the binaries**: `file SetConfig.exe` → PE32 x86. Dump imports to see it
   links `ftd2xx.dll` (FTDI D2XX) — that is the serial path to the unit.
4. **Read the resources/strings** of `LCode.exe` to see its own help text ("paste
   Long Coding…", "Short Coding (3,5,7 or 9 byte)…") — that identifies it as a
   coding decoder.
5. **Inspect the bundled `SwlFiles/`**: `Version.txt` (Continental header),
   `BlScript.cfg` (hardware match blocks), and the genuine `SWL.FLI`, confirm the
   disc-generation mechanism.
6. **Open the `.lbl`** files in a text editor — they are Ross-Tech/VCDS label files
   mapping coding bytes/bits to meanings for each part number.

A full decompile adds little: the coding protocol is the serial console already
documented in `FINDINGS.md`, so the practical result is that **the unit is codable
without the paid tool**.
