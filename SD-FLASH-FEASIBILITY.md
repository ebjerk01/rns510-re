# Flashing the RNS-510 from SD card — feasibility & plan

**Goal (user):** a small boot CD that starts the loader, then flash the firmware
payload from an SD card — like the map tool already does — so the failing CD
laser only has to read a few KB instead of 170 MB.

**Verdict: feasible — the SWL loader has native SD-card support built in.**
This is an undocumented but real capability, not a hack we have to invent.

## Evidence (from the decompressed SWL loader)

`SWL.FLI` is a zlib stream at offset 0x21 → 11.28 MB of VxWorks/PPC code
(the decompressed loader). It contains:

- **A full SD-card driver**: `DRV_SDCARD_*` (blockRead/Write, mRead/mWrite, LL/ML layers), `sdManagerTask` with `MSDMANAGER_MOUNT_VOLUME`.
- **DOS/FAT filesystem** (`dosFsLib.c`) and **cdromFs** — it can mount a FAT SD card and an ISO9660 CD.
- **SD mounted as `/sda` and `/sdb`** (`SD-Card already mounted SDA/SDB`, device roots `/sda`, `/sdb`).
- **Three SWL source listeners, one per medium**:
  - `dlsrcAddDVDServiceListener` (CD/DVD)
  - `dlsrcAddHDDServiceListener` (HDD)
  - **`dlsrcAddSdServiceListener` (SD card)** — "Adding of dlsrcAddSdServiceListener for SD Card"
- **A settable source path**: `dlsrcSetSWLPath` ("strlen sourcePath is %d, max is %d") and `dlProcessStruct.currentSourcePath`. The source base is a variable, not hardcoded to `/cddos`.
- **Source-agnostic flow**: `Software Download - Source activated, searching for SWL Image` → `Valid SWL Image found, starting SWL`. A media-type dispatch table (`No Function pointers for media type %d`).
- It can even pull SWL over **NFS** (`dlsPendSWLSources - error ... trying to mount NFS`) — a development feature, further proof the source is pluggable.
- A `/SWL_Source` path string and path templates built from a variable base:
  `%s/%s/%s/%s/CONFIG/DlScript.txt`, `%s/%s/%s/CRC.16`, `%s/%s/HwIdMap.txt`,
  `%s/%s/%s/PrjctMap.txt`.

So the loader is designed to detect a valid SWL tree on CD **or SD** (or HDD/NFS),
set the source path to it, and flash from there.

## Why this fixes the owner's failure

On the real unit: SWL 100%, HOST 100%, then **APPL stuck at 5%** → SWL media
error 010302. SWL.FLI (3.7 MB) and HOST load fine; the 170 MB APPL read
(A_HDD.FRG + FHDD6.FLI) off the worn CD laser fails. If APPL comes from SD, the
CD only has to deliver BLSCRIPT.CFG + SWL.FLI (a few MB that already work).

## Precedent

The map tool's `sd_to_hdd_fw.iso` is exactly this pattern: a tiny CD that makes
the unit pull large data from an SD card. **Getting a copy of that ISO (or the
"RNS maps-tool 2.0.2") is the Rosetta stone** — its `DlScript.txt` shows the
exact SD source path syntax and layout the loader expects, confirmed working.

## Experimental plan (lowest-risk first)

Prereq: a recovery path (`swl_fix.iso`) and ideally a serial console on the
26-pin connector (115200 8N1 — see `../README.md`), because the loader's own
debug prints (`currentSourcePath`, `searching for SWL Image`, `Valid SWL Image
found`) tell you exactly what it's doing and where it looks.

1. **Obtain `sd_to_hdd_fw.iso` / maps-tool** and read its `DlScript.txt` and SD
   layout. This likely answers the layout question outright.
2. **Reproduce the map SD→HDD copy** once (low risk, writes only to HDD) to
   confirm the unit reads the SD card as an SWL source at all.
3. **Build a minimal boot CD**: BLSCRIPT.CFG + SWL.FLI + VERSION.TXT + CRC.16,
   and a `CONFIG/DlScript.txt` that flashes APPL — but with the payload files
   on SD. Put the full SWL tree (APPS/.../FHDD6.FLI, A_HDD.FRG, CONFIG/DlScript,
   CRC.16, SPEECH/…) on a FAT32 SD card, mirroring the CD layout, possibly under
   `/SWL_Source/`.
4. **Watch the serial log.** If the loader reports the SD source activated and a
   valid SWL image found, it flashes from `/sda`. If it only ever looks at
   `/cddos`, we need to learn the trigger (SD listener may need a specific root
   dir or an `ECU_xx.ini` / `CP2SwlConfig.xml` present).

## Open questions / unknowns

- Exact SD layout: root vs `/SWL_Source/`; filename case on FAT (`DlScript.txt`
  vs the CD's uppercased `DLSCRIPT.TXT`).
- Whether the bootloader **ROM** can load SWL.FLI itself from SD (then no CD at
  all). Unknown — BLSCRIPT.CFG on the CD reads `//cddos/.../SWL.FLI`; the ROM
  stage's source scanning isn't in this image.
- Source precedence when CD and SD both hold a tree.
- Whether a DlScript-level command can call `dlsrcSetSWLPath` to redirect to SD
  (needs RE of the DlScript command table in the decompressed loader).
- Integrity: each tree has its own `CRC.16` (CRC16 only — no signature, see
  FINDINGS §flaws), so a custom SD tree is accepted as long as its CRC matches.
  We can compute it.

## Risk

Medium. We never reflash the bootloader or TEE. Worst case is a failed APPL
flash, recoverable with `swl_fix.iso` (the unit boots without a working
HDD/APPL). Do it with the battery on a charger. Confirm each step on the serial
console before the next.

## Donor radio as test mule (2026-11-04)

The owner has a donor RNS-510: shuts off after a few minutes on the bench and
boot-loops ~every 3 s; suspects missing CAN-gateway contact. Ideal mule — if the
SD-flash experiment bricks it, no loss.

**Likely cause of the donor reset (from loader strings), most probable first:**
1. **Under-voltage / weak bench supply.** The firmware monitors supply:
   `Detected under voltage ...`, `Detected under voltage for %d at %d/%d`,
   `DRV_VOLTAGE_GetNumberOfVlowHappened`. Inrush is large (~tens of A). A thin
   PSU browns out → hard 3 s reset loop. **Use a ≥10 A 12 V supply.**
2. **Clamp/ignition not wired.** `Clamp S on/off` sensing; needs switched +12 V
   on the ignition/clamp-15 pin in addition to permanent B+ and ground.
3. **Ignition-key/CAN timeout** (`setIgnitionKey`, `IgnitionKeyTimeout`,
   component-key mgmt). Usually causes limp/no-nav, not a 3 s hard loop — so CAN
   is a weaker suspect than power/clamp for this symptom.
4. Genuine hardware fault (power-rail caps etc.).

**Why the donor is still usable for the flash test even if it won't fully boot:**
SWL/update mode runs the loader *before* the theft-protection/CAN-dependent OS,
so it may be stable in SWL mode even when normal boot loops.

**Biggest unlock: attach the serial console (115200 8N1, 26-pin connector).**
The loader prints the exact reason live — under-voltage, clamp state, and for
the SD test `currentSourcePath`, `Source activated, searching for SWL Image`,
`Valid SWL Image found`. Diagnoses the donor AND validates the SD-flash path.

### Donor diagnosis — REVISED after new symptom (2026-11-04)
New detail: boots fully to the **PIN/SAFE screen**, holds there up to ~10 min,
then shuts off and boot-loops; once the loop intervals got **shorter and shorter**.
- Reaching the PIN screen and holding 10 min ⇒ power at boot is adequate; gross
  brownout is NOT the cause.
- **Decreasing reset intervals = thermal / failing power rail.** First run is from
  cold; once the board heats, a fault trips, and each restart begins warmer, so it
  fails sooner. Classic degrading-SMPS electrolytic-capacitor or overheating
  regulator signature — very common on ~2010 Continental RNS-510/MFD boards.
- Firmware has thermal sensing (`ThermalSensor`, `wdIdTemperature`, DVD/HDD temp)
  but **no software inactivity auto-off**; theft-protection blocking makes intervals
  LONGER not shorter — so this is hardware, not software and not CAN.
- The PIN screen is just component protection (donor from another car) — a red
  herring for the shutdown.
**Mule implications:** a full flash takes ~60 min; this donor will likely lose
power mid-flash → brick. Do NOT attempt a full flash on it as-is. It IS fine for
*validating* the SD mechanism: the first ~2 min are enough to see on serial
"Source activated → Valid SWL Image found → APPL reading from /sda". To make it a
real mule or to save it: **recap the power-supply board** (replace electrolytics)
and/or find the hot component (thermal/finger test in the first minutes).

## CONFIRMED by MapsTool itself (2026-11-04) — the working example

MapsTool-3.0.7 (Java, com.luxstudio90) embeds a complete SD2HDD boot package,
(extracted for analysis). It proves
the CD-small + SD-large split end to end:
- Boot CD (small, all the laser reads): BLSCRIPT.CFG, SWL/.../SWL.FLI (3.7MB),
  WA/*.WSH, WA/CTEST.OUT, HDD/.../CONFIG/DLSCRIPT.TXT, VERSION.TXT, CRC.16.
- DLSCRIPT just does `RUN_SHELL_SCRIPT 0 845 /cddos/WA/VIM.WSH`, EXPECTED_TIME 3379.
- VIM.WSH reads SD and copies to HDD (the proof): `sp xcopy("/sda/mapsdvd","/hdb2/dvd")`,
  `copy("/sda/maps/hddfiles.log","/hdb2/hddfiles.log")`. SD = `/sda`; shell has copy/xcopy/cd/mkdir/ld/sp.
- BLSCRIPT accepts 0x0002XXXX/0x0005XXXX — won't reject the 680C.

Build methods for firmware-from-SD:
- Method A (preferred, NAND): custom boot CD DLSCRIPT `LOAD_FIB <size> /sda/FHDD6.FLI` +
  `INSTALL_FRAGMENT <size> /sda/A_HDD.FRG`, payloads on FAT32 SD. One test left: confirm
  LOAD_FIB accepts a non-/cddos path (likely — /sda is mounted, paths are absolute).
- Method B (proven, data only): shell .WSH copy from /sda — what VIM.WSH does; HDD data not NAND.
Recipe: reuse this SWL.FLI+BLSCRIPT, write custom DLSCRIPT (Method A), put FHDD6.FLI+A_HDD.FRG
on FAT32 SD as /sda/..., recompute CRC.16, burn the tiny CD.

## SD card constraint for the unit (my-gti 3983)
C8/C9 (680C) predates SDXC support (a C10/C11/C12 feature). **Use an SDHC card
≤32 GB, FAT32** for the firmware-from-SD card. A 64 GB+ SDXC card may not be read
by this hardware. (Map tool guides also say max 32 GB SDHC.)
Target firmware for the final flash: **5269 modified** (max for 680C).
