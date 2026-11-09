# rns510-flashkit — getting started (CD + SD route)

Goal: get the RNS-510 running again by booting a **tiny CD** that pulls the heavy
work from an **SD card**. The CD is only ~4 MB (just the loader), so the worn laser
barely has to read.

**A CD is required** to bootstrap — the boot ROM reads the loader (`SWL.FLI`) from
CD-ROM; the SD card is only usable after the loader is running. SD-only is not
supported by the ROM.

## Building the discs

Build the two ISOs yourself with `pc/rns510_flashkit.py`, supplying your own genuine
`SWL.FLI` (extracted from an RNS-510 firmware ISO you already have). No firmware is
shipped in this repo. The loader you supply needs `MULTI_VERIFY_HDD`, the `/sda` SD
driver, and `hdTermShow*` — a 3xxx/5xxx-generation `SWL.FLI` has these.

## Hardware you need
- A CD/DVD burner. Burn **CD-R at the slowest speed** (or a **DVD-R** — different
  laser, often reads when the CD laser is marginal). Burn as a **disc image**, finalize, verify.
- An **SDHC card ≤32 GB, FAT32** (C8/C9 predates SDXC).
- A bench **12 V supply rated ≥10 A** + keep a charger on it. Updates draw hard.
- Strongly recommended: a **serial console** (115200 8N1 on the 26-pin connector,
  pinout in the main project README). The loader prints exactly what it's doing.
- Recovery disc `swl_fix.iso` ready, in case a unit won't boot.

## Order of operations

### Step 0 — serial console (do this first if you can)
Wire the console. It turns every step below from guesswork into reading the unit's
own log. Without it, the profile dump to SD is best-effort (see note).

### Step 1 — PROFILE (safe, read-only) — on a KNOWN-GOOD unit
This tells us which firmware is on NAND and the exact partition layout it expects —
which decides the `prepare` recipe.
1. Blank FAT32 SD card inserted.
2. Power the unit (good supply + charger).
3. Boot `rns510-profile.iso` (insert at power-on, or SETUP+EJECT+INFO to enter SWL).
4. Watch the serial log; it runs `hdTermShowDeviceIdentification`, `dosFsShow` per
   partition, and dumps coding/versions.
5. Capture the serial log (and the SD `/profile/` folder if present) — it drives the
   `prepare` recipe below.

> NOTE: the SD dump in `DUMP.WSH` has one unvalidated part — VxWorks shell has no
> `>` redirect, so capturing command output to SD isn't confirmed yet. **With the
> serial console you get everything regardless.** Once we confirm the capture
> method from the first run, the SD dump becomes self-contained.

### Step 2 — build the matching PREPARE disc
From the profile, set the correct `MULTI_VERIFY_HDD` recipe:
- 2xxx firmware (e.g. an as-shipped SW 2720 unit) → 2 partitions (67/33 %).
- 3xxx/5xxx firmware → 3 partitions (50/25/25 %).
The disc layout **must match the NAND firmware generation**, so build this from the
profile.

### Step 3 — PREPARE on a donor/mule first
If you have a spare or failing donor unit, use it as the first mule — validate quickly,
watching serial (a failing unit may only stay up a few minutes):
1. SD card holding the map data under `/mapsdvd/` (from a map DVD/source).
2. Boot `rns510-prepare.iso`. It runs `MULTI_VERIFY_HDD` (unit formats its own disk),
   then `COPYDATA.WSH` (`xcopy /sda/mapsdvd → /hdb2/dvd`).
3. Confirm on serial that it partitions and copies. Abort is fine once confirmed.

### Step 4 — PREPARE on the good unit
Same disc on the healthy unit, let it finish. The unit boots on its existing NAND
firmware and now has a correctly formatted disk (+ maps if you supplied them).

## If the NAND firmware itself is bad (unit won't boot)
Then we also flash firmware from SD. That path (`LOAD_FIB /sda/fw/FHDD6.FLI`) is
**unvalidated** — the lines are commented out in `scripts/prepare/DLSCRIPT.TXT`.
We confirm `LOAD_FIB`-from-`/sda` on the donor (serial) before enabling it, then
stage `FHDD6.FLI`+`A_HDD.FRG` on the SD under `/fw/`.

## About maps
To `prepare` with maps you need map data for `/sda/mapsdvd/` (from a genuine map
DVD or the map tool's output). Without it, the unit still **runs** — radio, media,
settings all work; nav just asks for a map disc. So you can get it "running" first,
add maps later.

## Safety recap
Battery on a charger; never interrupt power mid-flash; never touch the bootloader
or TEE; keep `swl_fix.iso` handy; validate on the donor before the good unit.
