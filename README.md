# RNS-510 — reverse-engineering notes

Reverse-engineering and firmware notes for the **VW RNS-510** navigation head unit
(Continental / ex-Siemens VDO, Wetzlar). The goal is to understand the platform well
enough to update, re-code, repair and safely modify a unit — and to document how the
flashing and coding actually work, since the public picture is scattered across
forum threads.

**Analysis only.** This repository contains no firmware binaries, no vendor tools,
no serial numbers, and no personal data. It builds heavily on the excellent krcenov
RE wiki (see *Sources*) and adds original firmware/loader analysis on top.

## What's here

| Document | Contents |
|---|---|
| [`README.md`](README.md) | This overview: the unit, the platform, how flashing works, compatibility, the real-world flash problem, and sources |
| [`FINDINGS.md`](FINDINGS.md) | The mod surface, security flaws, performance, the UI screen map, and the SWL loader's source-path / CRC internals |
| [`SD-FLASH-FEASIBILITY.md`](SD-FLASH-FEASIBILITY.md) | Flashing from an SD card instead of a dying CD laser — mechanism, the confirmed SD layout, and the plan |
| [`3810-analysis.md`](3810-analysis.md) | Firmware 3810: SD-flash, the USB/RNDIS diagnostic web server, CAF coding files, 3810-vs-5238 |
| [`can-bus-findings.md`](can-bus-findings.md) | CAN / vehicle-data: the ST10 gateway, what signals the unit uses (no powertrain data) |
| [`gateway-st10-findings.md`](gateway-st10-findings.md) | ST10 gateway (GATEWAY.FLI, C166): CAN handlers, DTC table, theft-protection state machine |
| [`map-inspection.md`](map-inspection.md) | West Europe V17 (CD_8557) map disc format, POI database, no speed-camera layer |
| [`poi-db-schema.md`](poi-db-schema.md) | POI.DB3 SQLite schema, the query catalog, and a custom-POI recipe |
| [`mapstool-findings.md`](mapstool-findings.md) | maps-tool 2.0.2 (Java): per-region SD→HDD disc generator, confirms the SD mechanism |
| [`fhdd6-version-diff.md`](fhdd6-version-diff.md) | What newer builds (5274/6276) add: overlay UI, SD import, DAB, a JReg settings layer |
| [`coding-reference.md`](coding-reference.md) | Consolidated coding: HU_CODING long coding, 0x400 registers, JReg settings, gateway items |
| [`ui-structure-findings.md`](ui-structure-findings.md) | Java UI structure: 822 menus, transition rules, the engineering screens (coding-gated) |
| [`deadzone-base-recovery.md`](deadzone-base-recovery.md) | The FHDD6 ">9 MB dead zone" resolved — the base holds; refs are GOT-based |
| [`5274-stock-vs-modified.md`](5274-stock-vs-modified.md) | What a "modified" firmware disc actually changes (5274): compatibility widening + CRC, not feature injection |
| [`6276-analysis.md`](6276-analysis.md) | The C14 6276 build, and why a `0x0006` BLSCRIPT block is *not* a compatibility guarantee |
| [`setconfig-analysis.md`](setconfig-analysis.md) | What the third-party "SetConfig" coding tool is and how it works (analysis only; no tool/keys/bypass) |
| [`partition-sizing.md`](partition-sizing.md) | Premade `MULTI_VERIFY_HDD` partition config + suggested sizes per common disk size |
| [`flashkit/`](flashkit/) | **Experimental, untested** builder for a CD+SD prepare/flash kit (builds the disc; ships no firmware) |
| [`SOURCES.md`](SOURCES.md) | Credits and prior work |
| [`artifacts/ui_screens_86.txt`](artifacts/ui_screens_86.txt) | The 86 UI screen/menu class names |
| [`tools/rns510_compat.py`](tools/rns510_compat.py) | Firmware ↔ hardware compatibility checker (WORKS/UNSTABLE/INCOMPATIBLE) |
| [`tools/rns510_serial.py`](tools/rns510_serial.py) | Serial console client: read/write coding + recover the theft PIN (needs on-unit verification) |
| [`tools/partition/`](tools/partition/) | Ready-to-copy `MULTI_VERIFY_HDD` partition config fragments |
| [`tools/ghidra_export.py`](tools/ghidra_export.py) | The Ghidra post-script used in the native analysis |

MIT-licensed (`LICENSE`). The tools are clean-room — built from this project's own
research, not copied from the prior repos; see `SOURCES.md`.

Primary external source — the krcenov RNS510-Map-Viewer wiki:
<https://github.com/krcenov/RNS510-Map-Viewer>

## The unit

Confirmed from the rear label (this project's reference unit):

| Field | Value |
|---|---|
| VW part | **1T0 035 680 C** (revision C → C8/C9 class, HW Vehicle code 0xC801, HW Radio 0006) |
| HW | **H42** |
| SW | **2720** (factory; a 2xxx generation = 20 GB music + 10 GB nav partitions, no POI partition) |
| Continental part | A2C53424523, variant VD1 |
| Made | 26.10.2010, Czech Republic |
| Serial | *(kept private — the radio login code derives from it)* |

## Platform at a glance

- **Application CPU:** Freescale **MPC5200B** (PowerPC 603e), **VxWorks 5.5**, Wind
  River gcc-2.96. NAND flash file system (TrueFFS) mounted at `/tffs0/`.
- **UI:** Java on the Wind River **Jeode EVM** (PersonalJava 1.1.1), packages
  `vdo.rns.*` / `vdo.nav.*` / `vdo.most.*`. Classes are "romized" (pre-linked), so
  ordinary decompilers do not recover them — this is the wall that blocks new
  on-screen UI with current public tooling.
- **Nav engine:** native PPC "navicore" / "Arriba" (`navcore.out`, `dbal.out`).
- **Gateway MCU:** ST10F276E (C166) in `VUCI/.../GATEWAY.FLI` — it bridges the car's
  comfort/infotainment CAN to the app (MOST/BAP) and holds the **theft-protection /
  PIN** state machine. (So the radio speaks CAN to the car through this MCU.)
- **Video in:** AD9883 / ADV7400 over I²C (DVD, TV, reversing camera).
- **Storage:** a standard MBR + FAT (Wind River DosFs 2.0) HDD/SSD holding maps,
  music and POI **data**. The bootable firmware lives in **NAND**, not on the disk.

### How flashing works (the SWL "Software-Loading" chain)

```
boot ROM ─ reads BLSCRIPT.CFG at the disc root (picks a script by HW ID 0x00xxXXXX)
         ─ LOAD_FLASH_IMAGE SWL/.../SWL.FLI → SET_BOOT_MODE 0x12 → REBOOT
         ─ SWL.FLI runs CONFIG/DLSCRIPT.TXT (per variant):
             RUN_SHELL_SCRIPT *.WSH      VxWorks shell: SetCoding, sp xcopy, format…
             INSTALL_FRAGMENT A_HDD.FRG  (≈85 MB → NAND)
             LOAD_FIB FHDD6.FLI          (≈85 MB app image → NAND)
             LOAD_ECU_BLOCK … GATEWAY.FLI / PQTABLE.FLI / MPEGAPPS.FLI
```

Everything that drives a flash — `BLSCRIPT.CFG`, `DLSCRIPT.TXT`, the `*.WSH` shell
scripts — is **plaintext and only CRC16-protected** (the CRC is advisory: a mismatch
logs "but only a warning" and continues). That is the root reason every community
"modified" disc works. The unit also **partitions and formats a blank disk itself**
(`MULTI_VERIFY_HDD` / `hdTermFormat`), so you do not pre-format the disk on a PC.
Details and the loader-internal evidence are in `FINDINGS.md`.

## Firmware compatibility

Match the **firmware generation to the hardware class** — this, not the bootloader's
acceptance, is what keeps a flash safe.

| Firmware | Hardware class |
|---|---|
| ≤ 5238 | C3–C12 |
| 5269 / 5274 | C6–C12 (5269 is the stable pick) |
| 5270+ | C10–C12 |
| 6276 | C14 |

For the reference **1T0035680C (C8/C9)** unit: **max modified firmware ≈ 5269**
(unmodified max 2840; factory 2660). **5269 modified is the target** for a final
flash. Do **not** flash 5270+/6276.

**Important caveat (see `6276-analysis.md`):** a `BLSCRIPT.CFG` containing a
`[0x0006XXXX]` block does **not** prove a disc is right for a 0006-class radio — the
C14 6276 build carries the same block. The block is a generic bootloader-acceptance
catch-all. Always judge compatibility from the firmware's `#VwSwPartNumber` /
`#Steckbrief` generation, cross-referenced with the table above.

Other practical rules:
- **5238 and factory-type images wipe the HDD / repartition** (music + maps lost).
- **SD-card limit:** SDXC (>32 GB) is a C10/C11/C12 feature; C8/C9 reads **SDHC
  ≤32 GB, FAT32** only. Size any SD-flash / map card accordingly.
- Enter update mode by hand with **SETUP + EJECT + INFO/MIC** (top-right button),
  engine off, on a stable supply. Recovery disc: `swl_fix.iso` (by josi).

## Hardware access — serial console

A VxWorks `tShell` runs at **115200 8N1** on the 26-pin video connector (N91-10930),
which is the key diagnostic and coding interface (it is what the SetConfig tool
drives — see `setconfig-analysis.md`).

| Video connector pin | Signal | PC DB9 pin |
|---|---|---|
| 14 (bottom row, far right) | GND | 5 |
| 1 (top row, far right) | unit RX (from PC TXD) | 3 |
| 2 (top row, second from right) | unit TX (to PC RXD) | 2 |

These pin numbers come from the krcenov diagram and the unlabelled pins on the label;
**verify them on the hardware.** Measure pin 2 against pin 14 first: about −5…−12 V at
idle means RS-232 levels; ~3.3 V means TTL and needs a 3.3 V USB-UART.

## The real-world problem on the reference unit

The reference unit **fails to flash**, and the analysis pinned down why.

- **On-screen:** SWL 100 %, HOST 100 %, then **APPL stuck at ~5 %**; the drive seeks
  continuously; after >24 h it ends in **SOFTWARE LOADING ERROR (010302) — "An error
  occurred related to the SWL Media."** Same result across several firmware versions
  and with two different disks (a KingSpec 128 GB PATA SSD and a wiped 20 GB HDD).
- **Diagnosis — it's the CD read, not the disk.** SWL and HOST are small (~1–2 MB)
  and load fine. APPL is the first *big* read: `A_HDD.FRG` + `FHDD6.FLI`, ≈170 MB off
  the disc **into NAND** (per the DLSCRIPT, nothing is written to the HDD at this
  step). A worn CD laser that can deliver a couple of MB but not 170 MB produces
  exactly this signature. The HDD step is never reached, so the SSD is not implicated.

**Two ways forward:**
1. **DVD-R** — the DVD laser is separate from the CD laser; burn the update to a
   Verbatim DVD-R at low speed, as a disc image, finalised and verified.
2. **SD-flash** — bootstrap with a tiny CD (only the few-MB `SWL.FLI`) and pull the
   big payload from an SD card, so the laser barely has to read. The SWL loader has
   native SD support and resolves its flash source from a settable path, not a
   hardcoded CD mount. This is the more robust fix; mechanism, the confirmed SD
   layout, and the plan are in **`SD-FLASH-FEASIBILITY.md`**.

Blank-disk prep for either route: the disk must be either truly blank (no MBR) or
carry the RNS partition layout; a PC-made MBR/NTFS/FAT layout is rejected, and the
drive must have no jumper. The SWL loader formats the blank disk itself.

## Appendix — anatomy of a 5238 update ISO

The 5238 "modified" disc (josi), as a concrete example of the structure above:

- `VERSION.TXT`: `#CD:P005.670.306`, 2012-10-19, "unofficial SWL CD by josi",
  Steckbrief C3/C4A/C5C/C6/C10/C12, CRC16 103e.
- `BLSCRIPT.CFG`: accepts `0x000201XX` / `0x0002XXXX` / `0x0005XXXX` / `0x0006XXXX`.
- Update order (`ECUORDER.TXT`): SWL, HOST, APPS, HDD, restart, RADIO, MPEG, VUCI
  (gateway), DAB, restart.
- APPL step: `INSTALL_FRAGMENT A_HDD.frg` (85,254,064 B) + `LOAD_FIB FHDD6.FLI`
  (85,658,916 B) + `UPDATE_SYS_CONFIG` / `CTEST.OUT` / `FIXCOD.WSH` — **all to NAND,
  nothing to the HDD.**
- HDD step: `MULTI_VERIFY_HDD 3 3 50 2 25 3 25 0 0`, then `FILE_UPDATE` of the speech
  packs into `/hdb2/speech/parts/`.
- `INFO/USER.CFG`: `HDD_FORMAT = 0`, `FORCE_HDD_FORMAT = 0`, `40GB_HDD = 1` — this
  disc does not force a disk format.

Extraction note: use `unar` for the RAR (the Debian 7z has no RAR codec), then
`7z x -tiso` for the ISO (without `-tiso`, 7z reads the broken UDF layer and recovers
only ~36 MB).

## FAQ

**My RNS-510 won't flash — it gets stuck at APPL (around 5%) then errors.**
That signature (SWL/HOST load fine, APPL stalls, SOFTWARE LOADING ERROR 010302 / "SWL
Media" error, the drive seeking) is almost always a **CD read failure, not the disk** —
APPL is the first ~170 MB read off the disc. Try a **DVD-R** (separate laser) or the
SD-flash route. See the "real-world problem" section above and `SD-FLASH-FEASIBILITY.md`.

**Can I flash the RNS-510 firmware from an SD card instead of a dying CD?**
The loader has native SD support and resolves its flash source from a settable path,
so a tiny ~4 MB boot CD can bootstrap and the payload can come from SD. Mechanism and
the confirmed SD layout: `SD-FLASH-FEASIBILITY.md` and `flashkit/`.

**Which firmware is safe for my unit?**
Match the firmware generation to the hardware class, not the bootloader's acceptance.
A `1T0035680C` (C8/C9) unit's safe max is ~5269; do not flash 5270+/6276. Use
`tools/rns510_compat.py` or see the compatibility section.

**How do I unlock video-in-motion / testmode / hidden menus?**
These are plaintext coding, not firmware patches: Testmode `0x21=01` and the 300 km/h
video-in-motion `0x0B3A=012C` (see `coding-reference.md`). The engineering/service
screens already exist and unlock via Testmode coding (`ui-structure-findings.md`).

**Is an HDD → SSD upgrade worth it, and what partition sizes?**
Yes — it removes seek latency (the biggest responsiveness gain). The unit formats the
disk itself; sizes are percentage-based. See `partition-sizing.md`.

## Sources

- krcenov RNS510-Map-Viewer wiki — firmware RE, boot chain, coding, serial console,
  map formats: <https://github.com/krcenov/RNS510-Map-Viewer>
- my-gti firmware repository (HW↔firmware map, version numbering, partition sizes):
  <https://web.archive.org/web/20200209030702/http://www.my-gti.com/3868/volkswagen-rns-510-firmware-download-repository>
- altechnative: <https://altechnative.net/vw-rns-510-firmware-maps-update/>
- paulroberts69 (HW table): <https://paulroberts69.wordpress.com/2015/10/01/upgrading-firmware-and-maps-on-vw-rns-510-satnav/>
- Remko Weijnen (logo.fli format, VERSION.TXT CRC16):
  <https://remkoweijnen.nl/blog/2011/09/27/rns-510-startup-logomy-thoughts/>
- bousqi/SMEG_PLUS — a related MPC5200/VxWorks/TFFS head unit, for comparison:
  <https://github.com/bousqi/SMEG_PLUS>
