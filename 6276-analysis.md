# RNS-510 FW 6276 — analysis (and what it teaches about compatibility)

Examined the `RNS_510_FW_6276_update` ISO (713,375,744 B). This is the newest
firmware generation in this project's sample set, and comparing it against the
older discs corrects a tempting but wrong assumption about hardware compatibility.

## Build identity
From `VERSION.TXT`:
- `Software Loading CD for CP2 based units (c) CONTINENTAL Wetzlar`, CdTreeBuilder 3.06
- `#CD:P005.789.302`, `#DATE:2014-07-01`, `#Author: MaGo`
- **`#Steckbrief: C_EU_33.276_t1 C14`** — a **C14** build
- `#VwSwPartNumber:` the newer part numbers only — `1T0035680R/S/T`, `3T0035680Q/R/S`,
  the `…686…` series, `2H0035686A`, etc. **No 680C.**
- `#VwSwIndex: 6276`, `#CRC16: 81c7`
- Image: `FHDD6.FLI` 85,828,184 B (vs 5238's 85,658,916 B — ~170 KB larger),
  `A_HDD.FRG` 85,267,992 B; 557 files total. New shell scripts present:
  `WA/RECOG_ON.WSH`, `WA/RECOVER.WSH`.

## The compatibility lesson: BLSCRIPT match ≠ hardware-appropriate
6276's `BLSCRIPT.CFG` has match blocks for `0x000201XX`, `0x0002XXXX`,
`0x0005XXXX` **and `0x0006XXXX`** (HW_MODULE 01.08 / HW_VERSION 01.01 /
CUSTOMER_PRODUCT 01.07) — **the same blocks as 5238 and 5274.**

That matters: 6276 is unambiguously a **C14** firmware (part numbers, Steckbrief),
yet it still carries the `[0x0006XXXX]` block. So the presence of a `0x0006XXXX`
block **does not** mean a disc is appropriate for a 0006-class (C8/C9) radio — the
block is a generic bootloader-acceptance catch-all shared across firmware
generations. The bootloader beginning to load is not the same as the flashed
application being right for the hardware.

**The authoritative compatibility signal is the firmware generation** — the
`#VwSwPartNumber` / `#Steckbrief` class, cross-referenced with the community
compatibility table:

| Firmware | Hardware class |
|---|---|
| ≤5238 | C3–C12 |
| 5269 / 5274 | C6–C12 (5269 the stable pick) |
| 5270+ | C10–C12 |
| **6276** | **C14** |

Per the my-gti table, a **1T0035680C (C8/C9)** unit's **max modified firmware is
~5269**. 6276 (C14) must **not** be flashed to it, BLSCRIPT match notwithstanding.

## RE value
Still useful despite being the wrong generation to flash: 6276 is the newest app
build here, so diffing its `FHDD6.FLI` against the 5238/5274 images is the best way
to spot late-era changes (new coding, menus, CAN handling, the added
`RECOG_ON`/`RECOVER` scripts). That diff is a follow-up.
