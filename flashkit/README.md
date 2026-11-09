# rns510-flashkit

> # ⚠️ UNTESTED — EXPERIMENTAL SCRIPTS ⚠️
> **These scripts have NOT been validated on real hardware. They can BRICK your
> RNS-510.** They were derived from reverse-engineering the SWL loader; several
> steps (output capture in `DUMP.WSH`, `LOAD_FIB` from `/sda`, the exact partition
> recipe per firmware generation) are **unconfirmed** and marked as such in the
> code. Treat everything here as a research starting point, not a finished tool.
>
> **If you run any of this, you do so entirely at your own risk.** Only use it on a
> unit you can afford to lose, keep a recovery disc (`swl_fix.iso`) ready, validate
> every step on a serial console first, and never interrupt power during a flash.
> No warranty of any kind. The authors are not responsible for any damage.
>
> This repo ships **no Continental/VW firmware** — you must supply your own
> `SWL.FLI` (and, for the firmware option, `FHDD6.FLI`/`A_HDD.FRG`) extracted from
> firmware you already have.

Tooling to prepare an RNS-510 HDD/SSD and (optionally) flash the application
firmware, using a **tiny boot CD + an SD card**, so a worn CD laser only has to
read a few MB. Private/experimental — **untested on hardware. Can brick a unit.**

## The architecture (grounded in RE of the real SWL loader)

Three facts from reverse-engineering `SWL.FLI` (the Software-Loading loader)
decide the whole design:

1. **The bootable firmware lives in NAND (`/tffs0`), not on the HDD.** `LOAD_FIB`
   writes `FHDD6.FLI` to NAND. The HDD only holds maps/music/POI **data** in a
   standard **MBR + FAT (Wind River DosFs 2.0)** layout (that's why a PC sees a
   FAT32 partition). So you cannot make a working radio by imaging an HDD alone;
   but a computer-prepared disk gets the data + partition layout right.
2. **The unit can partition and format a blank disk itself.** The loader has
   `dlsrcMultiVerifyHDD` / `dlsrcFormatHDD` / `dlsrcValidateHDD`, driven by one
   DLSCRIPT line: `MULTI_VERIFY_HDD <count> <fsType1> <pct1> <fsType2> <pct2> ...`
   The map tool uses `MULTI_VERIFY_HDD 3 3 50 2 25 3 25 0 0` = 3 partitions
   (50/25/25 %, FS-types 3/2/3). So the unit produces a guaranteed-compatible
   format — the PC doesn't have to replicate the exact FAT variant.
3. **The loader mounts the SD card as `/sda`** (full `DRV_SDCARD_*` driver +
   dosFs) and a `.WSH` shell script can `copy`/`xcopy` from `/sda` to `/hdb*`.
   This is exactly how the map tool's `VIM.WSH` works:
   `sp xcopy("/sda/mapsdvd","/hdb2/dvd")`.
4. **Custom discs run.** The tree `CRC.16` is advisory —
   `dlsFindCRCString - checksum was different - but only a warning`. The flashed
   image has its own enforced checksum, which passes with genuine firmware bytes.

**Net:** the computer only has to prepare a cheap FAT32 **SDHC ≤32 GB** card
(plain file copies). A tiny boot CD (just `SWL.FLI` + scripts) tells the radio to
partition/format its own disk and pull the data (and optionally the firmware)
from SD.

## Two tools

### 1. `profile` — read-out boot CD (do this FIRST, read-only)
A boot CD whose DLSCRIPT runs `scripts/profile/DUMP.WSH`, which dumps to the SD
card: the HDD partition table, drive identification/SMART, `dosFsShow` per
partition, installed coding, SW/HW/map versions, and directory listings.
Purpose: capture the exact recipe (partition sizes, FS types, data layout) your
firmware generation expects, from a **known-good** unit, before building/writing
anything. This is the "read out the old HDD, use that info" step.
Risk: low — reads the HDD, writes only to SD.

### 2. `prepare` — build-the-disk boot CD
A boot CD whose DLSCRIPT:
1. `MULTI_VERIFY_HDD <recipe>` — the unit partitions + formats the blank SSD.
2. `RUN_SHELL_SCRIPT .../COPYDATA.WSH` — `xcopy` maps/speech/POI from `/sda`.
3. *(optional)* `LOAD_FIB <size> /sda/FHDD6.FLI` — flash the NAND firmware from SD.

The PC builder (`pc/rns510_flashkit.py`) assembles the boot-CD ISO and the SD
tree from a user-supplied genuine `SWL.FLI` + `FHDD6.FLI` + map data.

## What the PC builder does
- Lays out the FAT32 SD card: `/mapsdvd/...`, `/speech/...`, optional firmware.
- Builds a minimal ISO9660 boot CD: `BLSCRIPT.CFG`, `SWL/.../SWL.FLI`,
  `CONFIG/DLSCRIPT.TXT`, the `WA/*.WSH`, a placeholder `CRC.16` (advisory).
- Never ships Continental firmware: you supply `SWL.FLI`/`FHDD6.FLI` extracted
  from your own firmware (see the main project README for extraction).

## Open items / must validate on hardware (in order)
1. **Output capture in DUMP.WSH.** *Resolved in RE (2026-11-04):* the loader has a
   native SD trace sink `/sda/trace/LogTraceOut.txt` — point the dump there instead
   of using shell `>` redirection. Still verify the file appears on a unit with the
   serial console attached.
2. **`LOAD_FIB` from `/sda`.** *Resolved in RE (2026-11-04):* LOAD_FIB reads from
   `dlProcessStruct.currentSourcePath` (set by `dlsrcSetSWLPath`), not a hardcoded
   `/cddos`, so a `/sda` path works once SD is the active source. Still confirm the
   first real flash on the donor mule.
3. **The MULTI_VERIFY recipe per firmware generation.** 2xxx = 2 partitions
   (`hdTermConfigurePartition(2,2,67,33,...)`), 3xxx+ = 3 partitions. Our 680C is
   SW 2720 (2xxx) now; target 5269 (3xxx-style, 3 partitions). The `profile` dump
   gives the authoritative numbers.
4. **SD size/geometry on C8/C9.** SDHC ≤32 GB, FAT32. 4 GB FAT32 file-size limit
   means raw partition images don't fit as one file — copy data as files, not images.

## Safety
- Always have `swl_fix.iso` (recovery) ready; keep the battery on a charger.
- Never reflash the bootloader or TEE. Worst case is a failed APPL flash,
  recoverable with the recovery disc (the unit boots without a working HDD/APPL).
- Validate each step on the serial console before the next. Use the **donor** as
  the first mule (short runs within its ~10-min window; see main project notes).

## Partition recipes per firmware generation (from real discs)
The `MULTI_VERIFY_HDD` FS-types differ by version — match the target firmware exactly:
- 1xxx/2xxx: `hdTermConfigurePartition(2,2,67,33)` → 2 parts, FS 3/2 (map tool FORMHDB1).
- 3810: `MULTI_VERIFY_HDD 3 3 50 2 25 2 25` → 3 parts 50/25/25, FS 3/2/2.
- 5238: `MULTI_VERIFY_HDD 3 3 50 2 25 3 25` → 3 parts 50/25/25, FS 3/2/3.
The 3rd (POI) partition's FS type changed 3810(2) → 5238(3). `scripts/prepare/DLSCRIPT.TXT`
carries the 5238 form; swap to the 3810 form if flashing a 3810-generation unit.
