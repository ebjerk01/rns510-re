#!/usr/bin/env python3
"""
rns510_compat.py — RNS-510 firmware ↔ hardware compatibility checker.

Clean-room tool built from this project's own research (see README.md,
6276-analysis.md, 5274-stock-vs-modified.md) and the public my-gti HW↔firmware
table. Given a VW part number and/or a firmware index, it returns a verdict:
WORKS / UNSTABLE / INCOMPATIBLE / UNKNOWN, with the reasoning.

It is informational only — verify before flashing, and remember a BLSCRIPT "0006"
match block does NOT by itself prove compatibility (see 6276-analysis.md).

Usage:
  rns510_compat.py --part 1T0035680C --fw 6276
  rns510_compat.py --part 1T0035680C          # show the safe ceiling for the unit
  rns510_compat.py --fw 5274                   # show which hardware a firmware targets
"""
from __future__ import annotations
import argparse
import re
import sys

# --- Hardware classes -------------------------------------------------------
# Mapping of VW part-number stems -> hardware class. "C-number" is the
# Continental hardware generation. Data from this project's research; extend as
# more datapoints are confirmed. Unknown stems return UNKNOWN rather than a guess.
#
# part stem (680<rev> / 686<rev>)         -> (class label, max_safe_fw_index)
HW_CLASSES = {
    # 1T0 035 680 x  (and sibling 3T0/7F0/7E0 ...). rev letter drives the class.
    "A": ("C3/C4", 3970),
    "B": ("C5/C6", 5238),
    "C": ("C8/C9", 5269),   # the reference unit: HW Vehicle 0xC801, HW Radio 0006
    "D": ("C10", 5274),
    "F": ("C11/C12", 5274),
    "G": ("C11/C12", 5274),
    "H": ("C11/C12", 5274),
    "J": ("C11/C12", 5274),
    "L": ("C11/C12", 5274),
    "P": ("C11/C12", 5274),
    "Q": ("C11/C12", 5274),
    # 680 R/S/T and the 686 series -> C14
    "R": ("C14", 6276),
    "S": ("C14", 6276),
    "T": ("C14", 6276),
}

# Firmware index -> (hardware class it targets, note). From VERSION.TXT Steckbriefe
# and this project's diffs. A firmware is "for" a class range; flashing a firmware
# meant for a NEWER class than the unit is the dangerous case.
FW_GENERATIONS = [
    (2840, "C3–C9", "2xxx; max UNMODIFIED for C8/C9"),
    (3970, "C3–C10", "3xxx generation"),
    (5238, "C3–C12", "5xxx; broad compatibility"),
    (5269, "C6–C12", "5xxx; the stable pick, and the max MODIFIED safe for C8/C9"),
    (5274, "C6–C12", "5xxx; > 5269, treat as out-of-range on C8/C9"),
    (6276, "C14", "C14 only — do NOT flash on C8/C9 or C10/C12"),
]


def part_rev(part: str) -> str | None:
    """Extract the trailing revision letter from a part number like 1T0035680C."""
    p = re.sub(r"[^0-9A-Za-z]", "", part).upper()
    m = re.search(r"03568[06]([A-Z])$", p)   # ...035680<rev> or ...035686<rev>
    if m:
        return m.group(1)
    m = re.search(r"([A-Z])$", p)
    return m.group(1) if m else None


def class_for_part(part: str):
    rev = part_rev(part)
    if rev and rev in HW_CLASSES:
        return rev, HW_CLASSES[rev]
    return rev, None


def verdict(part: str | None, fw: int | None) -> int:
    print(f"RNS-510 compatibility check")
    print("-" * 48)

    cls = max_fw = None
    if part:
        rev, info = class_for_part(part)
        if info:
            cls, max_fw = info
            print(f"Part {part}: hardware class {cls}, safe firmware ceiling ~{max_fw}")
        else:
            print(f"Part {part}: UNKNOWN hardware class"
                  f"{f' (rev {rev})' if rev else ''} — not in the dataset.")

    if fw is not None:
        gen = next((g for g in FW_GENERATIONS if g[0] == fw), None)
        if gen is None:
            # nearest-known generation for context
            gen = min(FW_GENERATIONS, key=lambda g: abs(g[0] - fw))
            print(f"Firmware {fw}: not an exact known index; nearest known is "
                  f"{gen[0]} (targets {gen[1]}).")
        else:
            print(f"Firmware {fw}: targets {gen[1]} — {gen[2]}")

    print("-" * 48)

    if fw is None and max_fw is not None:
        print(f"VERDICT: this {cls} unit is safe to flash up to ~{max_fw}. "
              f"Pass --fw <index> to check a specific firmware.")
        return 0
    if part is None and fw is not None:
        print("VERDICT: pass --part <number> to check against a specific unit.")
        return 0
    if part is None or fw is None or max_fw is None:
        print("VERDICT: UNKNOWN — need a known part number and a firmware index.")
        return 2

    if fw <= max_fw:
        print(f"VERDICT: WORKS — {fw} is within the {cls} safe ceiling (~{max_fw}).")
        return 0
    # over the ceiling: is it merely the next notch, or a whole class too new?
    if fw <= 5274 and max_fw >= 5269:
        print(f"VERDICT: UNSTABLE — {fw} is above the {cls} safe max (~{max_fw}). "
              f"Community consensus caps C8/C9 at 5269; flashing higher is risky.")
        return 1
    print(f"VERDICT: INCOMPATIBLE — {fw} targets newer hardware than {cls}. "
          f"Do NOT flash (a BLSCRIPT 0006 match does not make it safe).")
    return 3


def main() -> int:
    ap = argparse.ArgumentParser(description="RNS-510 firmware/hardware compatibility check")
    ap.add_argument("--part", help="VW part number, e.g. 1T0035680C")
    ap.add_argument("--fw", type=int, help="firmware index, e.g. 5269")
    a = ap.parse_args()
    if not a.part and a.fw is None:
        ap.print_help()
        return 2
    return verdict(a.part, a.fw)


if __name__ == "__main__":
    sys.exit(main())
