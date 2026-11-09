# maps-tool 2.0.2 (Java) — decompilation findings

`maps-tool-2.0.2.exe` is a launch4j-wrapped Java app (package
`com.luxstudio90.mapstool`), ProGuard-obfuscated (single-letter classes). The logic
is obfuscated, but the string constants and **bundled resources** are not — and they
carry the whole SD→HDD mechanism.

## What it is
A **per-region SD→HDD map-install disc generator**. Given a map source, it builds a
small boot ISO that boots the SWL loader and copies the map data from SD to the HDD.
Its own UI strings: "Generate firmware file for region {0}", "Preparing firmware for
map region", "write ISO firmware for region", menu items Western/Eastern Europe.
(Here "firmware file" = the boot ISO, not NAND firmware.)

## Bundled boot tree (`fw/SD2HDD/`)
A complete, ready SWL boot tree:
`BLSCRIPT.CFG` (2524 B), `DLSCRIPT.TXT`, `VERSION.TXT`, `HWIDMAP.TXT`, `PRJCTMAP.TXT`,
`CRC.16`, `WA/*.WSH` (incl. `CTEST.OUT`, `FORMHDB2.WSH`, `DEL_FOLD.WSH`, …) and a
genuine Continental **`SWL/SILVER_1/RNSMIDEC/SWL/SWL.FLI`** (3.74 MB — copyrighted,
not redistributed here; sha matches the `EU_sd_to_hdd_fw.iso` loader). So the app is
the generator behind the `*_sd_to_hdd_fw.iso` discs.

`ECUORDER.TXT`: `LOAD_LIBRARY CTEST.OUT` → `FORMHDB2.WSH` (delete old maps) → restart
→ `DEL_FOLD.WSH` → `HDD` → restart → `DEL_FOLD.WSH` → restart → `FINISHED_DOWNLOAD`.

## Per-region VIM.WSH (the SD→HDD copy script)
Four regional variants (`fw/EEU`, `fw/EU`, `fw/AUNZ`, `fw/NA`), all doing
`sp xcopy("/sda/mapsdvd","/hdb2/dvd")` + `copy("/sda/maps/hddfiles.log",…)` and
setting Testmode `0x21=01` + 300 km/h `0x0B3A=012C`. Differences:
- **EU and EEU are identical** — full `telemat/tmc2/{lan,loc}` (TMC traffic) tree.
- **AU-NZ** comments out the `telemat/tmc2/lan/loc` dirs — **no TMC** in that region.
- **NA** adds `mkdir("SIRIUS")` — SiriusXM data — and a different telemat layout.

So the SD card's `/sda/mapsdvd/` tree is region-shaped, and the HDD `/hdb2/dvd/`
directory skeleton the script creates matches it.

## Confirms (and bounds) the SD mechanism
- The maps-tool copies **map data only** (`/sda/mapsdvd` → `/hdb2/dvd`) — it does
  **not** flash NAND firmware. So the public tool proves Method B (data from SD); the
  firmware-from-SD path (`LOAD_FIB /sda/FHDD6.FLI`) remains this project's extension.
- The SD layout and the boot-CD template match exactly what `SD-FLASH-FEASIBILITY.md`
  recovered from the static ISO — now confirmed from the generator itself, with the
  per-region shape documented.
