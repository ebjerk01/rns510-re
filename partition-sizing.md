# HDD/SSD partition sizing

The RNS-510 **partitions and formats the disk itself** during a flash — you never
partition it on a PC. One DLSCRIPT line controls the layout:

```
MULTI_VERIFY_HDD <count> <fsType1> <pct1> <fsType2> <pct2> [<fsType3> <pct3>] 0 0
```

- `count` — number of partitions.
- each `<fsTypeN> <pctN>` pair — a partition's filesystem-type code and its size as a
  **percentage of the whole disk**. The percentages must add up to 100.
- the trailing `0 0` is padding (keep it).

Because sizing is by **percentage, not absolute size**, the same line gives
proportionally larger partitions on a larger disk — you rarely need to change the
numbers; you just fit a bigger disk. The loader validates each partition and
reformats any that are missing or the wrong filesystem type.

## Match the partition count + FS types to the firmware generation

This is the part that must be right. The partition **count** and the **FS-type
codes** are fixed per firmware generation — using the wrong form will leave the unit
unable to mount its data:

| Firmware generation | Partitions | Stock line |
|---|---|---|
| 1xxx / 2xxx | 2 (maps, music/speech) | `MULTI_VERIFY_HDD 2 3 67 2 33 0 0` |
| 3xxx (e.g. 3810) | 3 (maps, music, POI) | `MULTI_VERIFY_HDD 3 3 50 2 25 2 25 0 0` |
| 5xxx (e.g. 5238/5269) | 3 (maps, music, POI) | `MULTI_VERIFY_HDD 3 3 50 2 25 3 25 0 0` |

Note the only difference between the 3810 and 5238 three-partition forms is the
**third (POI) partition's FS type** — `2` on 3810, `3` on 5238/5269. Match it to the
firmware you are flashing. Ready-to-copy fragments are in
[`tools/partition/MULTI_VERIFY_HDD-examples.txt`](tools/partition/MULTI_VERIFY_HDD-examples.txt).

Partition roles (by convention): **P1 = maps**, **P2 = music / speech**, **P3 = POI**
(3xxx+ only). Keep the maps partition comfortably larger than your map data (a West
Europe set is ~4–5 GB; a full Europe set is larger).

## Suggested sizes per common disk size (at the stock ratios)

Nominal GB (decimal); the usable space after FAT formatting is a little less. The
same percentages, applied to whatever disk you fit:

**Three partitions (3xxx/5xxx — 50 / 25 / 25):**

| Disk | P1 maps (50%) | P2 music (25%) | P3 POI (25%) |
|---|---|---|---|
| 20 GB | 10 | 5 | 5 |
| 32 GB | 16 | 8 | 8 |
| 40 GB | 20 | 10 | 10 |
| 64 GB | 32 | 16 | 16 |
| 120 GB | 60 | 30 | 30 |
| 128 GB | 64 | 32 | 32 |

**Two partitions (1xxx/2xxx — 67 / 33):**

| Disk | P1 maps (67%) | P2 music (33%) |
|---|---|---|
| 20 GB | 13.4 | 6.6 |
| 32 GB | 21.4 | 10.6 |
| 40 GB | 26.8 | 13.2 |
| 64 GB | 42.9 | 21.1 |
| 120 GB | 80.4 | 39.6 |
| 128 GB | 85.8 | 42.2 |

The original factory disks were 30–40 GB, so 32–40 GB already matches the stock
experience; 64–128 GB just gives proportionally more music space.

## Custom ratios (optional, experimental)

To re-balance — e.g. more music space — change the percentages, keeping the
**count and FS types** from the table above and keeping P1 large enough for your
maps. These are for 5xxx firmware (FS types `3 2 3`); percentages must sum to 100.
Config line: `MULTI_VERIFY_HDD 3 3 <P1> 2 <P2> 3 <P3> 0 0`.

| Profile | maps / music / POI | Config line | 64 GB (P1/P2/P3) | 128 GB (P1/P2/P3) |
|---|---|---|---|---|
| Stock | 50 / 25 / 25 | `3 3 50 2 25 3 25 0 0` | 32 / 16 / 16 | 64 / 32 / 32 |
| More music | 40 / 40 / 20 | `3 3 40 2 40 3 20 0 0` | 25.6 / 25.6 / 12.8 | 51.2 / 51.2 / 25.6 |
| Max music | 30 / 50 / 20 | `3 3 30 2 50 3 20 0 0` | 19.2 / 32 / 12.8 | 38.4 / 64 / 25.6 |
| Music, tiny POI | 45 / 45 / 10 | `3 3 45 2 45 3 10 0 0` | 28.8 / 28.8 / 6.4 | 57.6 / 57.6 / 12.8 |
| Big maps (full Europe) | 60 / 20 / 20 | `3 3 60 2 20 3 20 0 0` | 38.4 / 12.8 / 12.8 | 76.8 / 25.6 / 25.6 |
| Balanced | 40 / 35 / 25 | `3 3 40 2 35 3 25 0 0` | 25.6 / 22.4 / 16 | 51.2 / 44.8 / 32 |

Guidance:
- **P1 (maps)** must stay ≥ your map data (West Europe ≈ 4–5 GB; a full Europe set is
  larger). Avoid dropping P1 below ~30 % on disks under 64 GB.
- **P3 (POI)** only holds `POI.db3` (a few hundred MB), so a small POI share is fine.
- All custom ratios are **not validated on hardware** — the firmware may assume the
  stock split in places, so verify maps + music still load after flashing. Stay with
  the stock 50 / 25 / 25 unless you have a reason to change it.

## Hard limits and safety

- **~137 GB (LBA28) cap** on the PATA interface — do not fit a disk larger than
  ~120–128 GB; the unit cannot address beyond LBA28.
- The disk must be **either truly blank (no MBR) or already carry the RNS layout**; a
  PC-made MBR/NTFS/FAT layout is rejected. The drive must have **no jumper**.
- The percentages are of the **whole disk**; they must sum to 100.
- Changing partitioning is part of a flash, which is brick-risk — keep `swl_fix.iso`
  ready and the unit on a stable supply. See the main README and `FINDINGS.md`
  ("HDD partitioning & format") for the mechanism.
