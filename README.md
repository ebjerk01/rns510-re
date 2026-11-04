# RNS-510 project

The VW RNS-510 navigation head unit (Continental / ex-Siemens VDO, Wetzlar).
Started 2026-11-04. The firmware is downloading on the PC (`a PC`,
`~/Downloads`).

## The unit (confirmed from the rear label)

| Field | Value |
|---|---|
| VW part | **1T0 035 680 C** (revision C, so C8/C9 class, HW code 0xC801 per the GPS Underground table) |
| HW | **H42** |
| SW | **2720** (factory, 2xxx generation: 20 GB music + 10 GB nav partitions, no POI partition) |
| Continental part | A2C53424523, variant VD1 |
| Made | B 26.10.2010, Czech Republic |
| Serial | [redacted — radio code derives from it] |

**Upgrade path:** going from 2720 to 5238 is inside "C3-C12 up to 5238" and will repartition the disk (wipes music and maps). my-gti: upgrading from 1xxx/2xxx straight to 3930/3970 does *not* repartition, but 5238 is a factory-type image, so it should. Confirm in the ISO.

### Rear connectors (from the label)

- **Quadlock D (power):** 16 = SAFE, + (power), ground, Amp (remote), CAN- / CAN+.
- **Quadlock A (speakers):** LR, LF, RF, RR ±.
- **Quadlock B:** clock in, data in, data out, CD L/R, AUX L/R + grounds.
- **Quadlock C:** TEL R±/L±, TEL MUTE, MIC in±/out±.
- **26-pin video connector** (the N91-10930 in the krcenov diagram): 2 rows of 13.
  - Top row is pins 1-13 from right to left; bottom row is 14-26 from right to left.
  - Labelled pins: RGB/sync in and out, video ground, R/L audio in, NF.
  - **Pins 1-3 and 14-16 (rightmost three in each row) are unlabelled.** The debug UART is there:

| Video connector pin | Signal | DB9 pin (PC side) |
|---|---|---|
| 14 (bottom row, far right) | GND | 5 |
| 1 (top row, far right) | unit RX (from PC TXD) | 3 |
| 2 (top row, second from right) | unit TX (to PC RXD) | 2 |

- Serial settings: 115200 8N1, VxWorks tShell.
- The source diagram wires the unit straight to a PC DB9, which suggests RS-232 levels, but this is not verified.
- **Measure before connecting:** check pin 2 against pin 14 with a multimeter. About -5 to -12 V at idle means RS-232; 3.3 V means TTL and needs a 3.3 V USB-UART.
- The pins come from the krcenov diagram and match the unlabelled pins on the label. They are still unverified on the real unit.

Still to check: hold SETUP for 10-30 s for the version-info menu (the map version is not on the label). On 2720 the menu may not exist; it arrived with 3xxx.

## This repository

Documentation and analysis only. Firmware binaries, the vendor map tool, and the
cloned reference material are **not** included (copyright + size).

| Path | What |
|---|---|
| `README.md` | This overview: platform facts, compatibility, update procedure |
| `FINDINGS.md` | Mod surface, security flaws, performance, the UI screen map |
| `SD-FLASH-FEASIBILITY.md` | Flashing from SD card — mechanism and feasibility |
| `SOURCES.md` | Credits and prior work |
| `artifacts/ui_screens_86.txt` | The 86 UI screen/menu class names |
| `tools/ghidra_export.py` | Ghidra post-script used in the native analysis |

The primary external RE source is the krcenov RNS510-Map-Viewer wiki:
<https://github.com/krcenov/RNS510-Map-Viewer>

## Platform facts (from krcenov's RE wiki, built on the 5238 SWL CD)

- **APPS CPU:** Freescale **MPC5200/5200B** (PowerPC 603e core).
  - OS: **VxWorks 5.5**.
  - Toolchain: Wind River gcc-2.96.
  - Flash file system: TrueFFS, mounted at `/tffs0/`. NAND is a Samsung K9F12088U0.
  - HDD partitions: `/hdb1` (maps), `/hdb2` (music, speech) and, from 3xxx, a POI partition.
- **UI:** Java on the Insignia/Wind River **Jeode EVM** (PersonalJava 1.1.1).
  - Packages are `vdo.rns.*`, `vdo.nav.*` and `vdo.most.*`.
  - Most classes are "romized" (pre-linked), so ordinary decompilers do not work. That blocks UI modding with known tools.
- **Nav engine:** native PPC code called "navicore" / "Arriba" (`/tffs0/lib/arriba/navcore.out`, `dbal.out`).
- **Gateway MCU:** ST10F276E (C166).
  - Firmware: `VUCI/.../GATEWAY.FLI`.
  - It holds the MOST/CAN gateway and the **theft protection / PIN** state machine.
  - Disassembler: `hn/c166-dis`.
- **Possible safety MCU:** TMS470MF04207 (Cortex-M3). Not confirmed.
- **Video in:** AD9883 / ADV7400 over I2C. Sources are DVD, TV and RVC.
- **Serial debug console:** VxWorks `tShell`, 115200 baud, on a 26-pin connector (N91-10930), with pin 14 = GND.
  - See the krcenov wiki: <https://github.com/krcenov/RNS510-Map-Viewer/wiki/Theft-Protection-and-the-CAN-Gateway>.
  - The RX/TX pin numbers come from a diagram, so verify them on the hardware.
- **Bluetooth:** Parrot module.

### Update / boot chain (SWL = Software Loading CD)

```
boot ROM -> BLSCRIPT.CFG (disc root, chooses the script by HW ID 0x000201XX...)
         -> LOAD_FLASH_IMAGE SWL/.../SWL.FLI, SET_BOOT_MODE 0x12, REBOOT
         -> SWL.FLI runs CONFIG/DLSCRIPT.TXT (per variant)
              RUN_SHELL_SCRIPT *.WSH   (VxWorks shell scripts: sp xdelete, SetCoding...)
              INSTALL_FRAGMENT A_HDD.FRG ("ZZZZ" container, CRC-CCITT)
              LOAD_FIB FHDD6.FLI       (85.6 MB app image, AA55AA55 wrapper)
              LOAD_ECU_BLOCK ... GATEWAY.FLI / PQTABLE.FLI / MPEGAPPS.FLI
```

- `VERSION.TXT` carries `#VwSwIndex`, `#VwSwPartNumber` and `#CRC16`.
  - Remko Weijnen worked out the CRC16; tools such as RNS 510 Editor exist.
  - Update images are marked `.301` and keep data. Factory images are marked `.901` and wipe the HDD and repartition it.
- Entering update mode by hand: **SETUP + EJECT + INFO/MIC** (top right button).
- Recovery: `swl_fix.iso` (3.75 MB, by Josi) for SWL / Gateway error 202 hangs.

## Firmware compatibility (my-gti)

| HW | Max firmware |
|---|---|
| C3-C12 | 5238 |
| C6-C12 | 5274 (5269 is often called more stable) |
| C14 | 6276 |

**Definitive HW↔firmware map (my-gti 3983):**
- **The unit 1T0035680C (C8/C9, HW Vehicle 0xC801, HW Radio 0006): max MODIFIED firmware = 5269.** Unmodified max 2840; from-factory 2660.
- 5270 = C10/C11/C12 (0xCA01/0xCC01, 680D/F/G/H/J/L/P/Q). 6270 = C14. **Do NOT flash 5270+/6270 on the 680C.**
- 5238 (what we have) is compatible but not the newest; **5269 modified is the target firmware for the final flash.**
- **SD-card limit:** 2TB SDXC support is a C10/C11/C12 feature. The C8/C9 likely reads **SDHC (≤32 GB) FAT32 only** — size the SD-flash card accordingly.

- The 5238 Josi SWL CD names C3/C4A/C5C/C6/C10/C12 in `#Steckbrief`, but not C8.
- **Before burning anything, check that `BLSCRIPT.CFG` matches the HW ID.**
- **5238 wipes maps.**
- Dell download in progress: `RNS_510_FW_5238_update_modified.rar`, Josi's modified 5238 (VIM + test mode), about 493 MB.

## Update procedure (consensus from the sources)

1. Keep the battery on a charger or a stable supply for the whole update (about an hour). The unit draws heavy current in peaks, so a weak supply can sag and interrupt the flash — which risks bricking it.
2. Burn a CD-R at the lowest speed.
3. Engine off. Enter update mode, insert the disc and confirm.
4. Set 24-hour clock mode. "Clamp state" errors mean the unit did not reboot into update mode correctly.
5. Maps: maps-tool 2.0.2 (not 2.1.3 for v17) copies them to a FAT32 SDHC card (32 GB or less). Then boot `sd_to_hdd_fw.iso`. The progress display stays at 31% while it copies.

## Sources

- https://altechnative.net/vw-rns-510-firmware-maps-update/
- https://paulroberts69.wordpress.com/2015/10/01/upgrading-firmware-and-maps-on-vw-rns-510-satnav/ (HW table in the post)
- https://web.archive.org/web/20200209030702/http://www.my-gti.com/3868/volkswagen-rns-510-firmware-download-repository
- my-gti 3374 (version numbering, partition sizes) and 3869 (5238 VERSION.TXT)
- https://github.com/krcenov/RNS510-Map-Viewer and its wiki: firmware RE, boot chain, coding, serial console, map formats
- https://remkoweijnen.nl/blog/2011/09/27/rns-510-startup-logomy-thoughts/ (logo.fli format, VERSION.TXT CRC16)
- https://github.com/bousqi/SMEG_PLUS (a related MPC5200/VxWorks/TFFS head unit, for comparison)

## Open questions / next steps

1. Read the label and the version-info menu to get the real HW index, SW version and map version.
2. Obtain the firmware, check the hash, and extract the RAR then the ISO with 7z.
3. Inventory the ISO: `VERSION.TXT`, `BLSCRIPT.CFG` (does it match the HW ID?), DLSCRIPTs and `.WSH` files.
4. Diff it against the original 5238 to see what Josi's "modified" disc changes.
5. The owner decides the goal: plain update, maps, or deeper RE / mods (logo, coding, serial console).

## SSD swap (2026-11-04, in progress)

- **Hardware:** the owner fitted a KingSpec 128 GB PATA SSD. 128 GB is about 119 GiB, under the LBA28 limit of 137 GB, so size should be fine.
- **Symptom:** flashing gets stuck at the APPL or HDD step. The same happens with a wiped 20 GB HDD, so the SSD itself is probably not the cause.
- **Known from forums:**
  - The unit only accepts a disk that is either truly blank (no MBR at all) or carries the RNS partition layout. A PC-made MBR or NTFS/FAT layout is rejected.
  - The drive must have no jumper.
  - Every SWL loader can partition/format a blank disk itself (`MULTI_VERIFY_HDD` / `hdTermFormat`); see FINDINGS.md, "HDD partitioning & format". The old advice to "run SWL 3810" is a fallback, not a requirement.
  - Cloning an original RNS disk image (Acronis, AOMEI, Paragon) also works.
- **The reading of the 5238 SWL (krcenov):** the HDD ECU step runs `MULTI_VERIFY_HDD`, then `FILE_UPDATE /hdb2/speech/...`. With no `/hdb2` it has nowhere to write, which fits "stuck at HDD". Verify this in the ISO.
- **Plan:**
  1. Zero the start and end of the drive on Linux, through an IDE-to-USB adapter.
  2. Remove the jumper.
  3. Run SWL 3810 so the unit partitions the disk.
  4. Then go up to 5238.
- **Recovery** if the unit won't boot: `swl_fix.iso`.

### Diagnosis from the on-screen loading status

- **Disc shown:** `#CD:P005.157.301`, `#DATE:2010-11-26`, a `.301` update disc from the 2xxx era.
- **Progress:** SWL 100%, HOST 100%, then **APPL stuck at 5%**. HDD, RADIO, MPEG and GATEWAY all stayed at 0%. Total 29%, "52 mins" remaining.
- **Behaviour:** the drive seeked the whole time. After more than 24 h it ended in **SOFTWARE LOADING ERROR (010302) / SWL ERROR, "An error occurred related to the SWL Media"**.
- **Same result** with several firmware versions, and with both the SSD and the 20 GB HDD.
- **Conclusion: a CD read failure, not the disk.**
  - SWL and HOST are small (about 1-2 MB) and load fine.
  - APPL is the first big read: A_HDD.FRG plus FHDD6.FLI, about 170 MB from the CD. Per the krcenov DLSCRIPT it writes to NAND, not to the HDD.
  - The HDD step was never reached, so the SSD has not been tested yet.
- **Suspects, most likely first:** a weak or dirty laser in the RNS DVD loader; the burn media or burn quality; a shared ATA bus with the SSD (low odds, but test with no disk fitted).
- **From the owner's memory, not checked:** on a PC, through a USB-PATA adapter, the drive showed partitions, and the FAT32 partition had content. If the unit created them, its disk access works. Check the partition layout read-only on the PC next time the disk is available.
- **Next test:** burn the update to DVD-R, Verbatim at 4x, written as a disc image, finalised and verified. The DVD laser is separate from the CD laser.

## 5238 modified ISO, checked 2026-11-04 (the 5238 ISO)

- **RAR:** sha256 `20292e13588fd815756ed8ed80387f3c05ad0792ef39e0de4bc424cf7b2213c1`, the same on the PC and on the workstation.
- **ISO:** `RNS_510_FW_5238_update_modified.iso`, 717,000,704 bytes, sha256 `ea9db70bfd1db4a6b6bade33a8d48c258e91266add5f554e6799c6a212a93581`. It fits an 80-min CD-R (737,280,000 bytes) and of course a DVD-R.
- **How to extract:** `unar` for the RAR (the Debian 7z has no RAR codec), then `7z x -tiso` for the ISO. Without `-tiso`, 7z reads the broken UDF layer and gets only 36 MB.
- **`VERSION.TXT`:** `#CD:P005.670.306`, dated 2012-10-19, "unofficial SWL CD by josi", Steckbrief C3/C4A/C5C/C6/C10/C12, CRC16 103e.
- **`BLSCRIPT.CFG`:** accepts product `0x000201XX` / `0x0002XXXX` / `0x0005XXXX` / `0x0006XXXX` with any HW version, so the boot loader will not reject the unit.
- **Update order (`ECUORDER.TXT`):** SWL, HOST, APPS, HDD, restart, RADIO, MPEG, VUCI (gateway), DAB, restart.
- **The APPL step** (e.g. `APPS/SILVER_1/EURSBHDD/CONFIG/DLSCRIPT.TXT`):
  - `DEL_LANG.WSH` (flash only)
  - `INSTALL_FRAGMENT A_HDD.frg` (85,254,064 bytes)
  - `LOAD_FIB FHDD6.FLI` (85,658,916 bytes)
  - `UPDATE_SYS_CONFIG`, `CTEST.OUT`, `FIXCOD.WSH`, then one `LANG_xx`/`RECOG_xx` FRG pair
  - All of it goes to NAND (`/tffs0`) and **none of it touches the HDD**. Stuck at APPL 5% therefore means the unit is reading A_HDD.frg from the disc.
- **The HDD step:** `MULTI_VERIFY_HDD 3 3 50 2 25 3 25 0 0`, `DEL_OUT.WSH`, then `FILE_UPDATE` of the 14 `UVO_*.ZIP` packs into `/hdb2/speech/parts/`.
- **`INFO/USER.CFG` build flags:** `HDD_FORMAT = 0`, `FORCE_HDD_FORMAT = 0`, `40GB_HDD = 1`, HARDWARE_C6/C10/C12 = 1. This disc does not force a disk format.
