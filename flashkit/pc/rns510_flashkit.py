#!/usr/bin/env python3
"""
rns510-flashkit PC builder.

Assembles the two artifacts for an RNS-510 HDD/SSD prep + optional firmware flash:
  * a minimal bootable SWL CD image (ISO9660), and
  * the FAT32 SD-card tree with the map/speech data (+ optional firmware).

It ships NO Continental firmware. You supply genuine SWL.FLI (and, for the
firmware-flash option, FHDD6.FLI / A_HDD.FRG) extracted from your own RNS-510
firmware ISO. See the main project README for extraction (7z -tiso / unar).

STATUS: experimental, UNTESTED on hardware. Read flashkit/README.md first.
Requires `xorriso` (or `genisoimage`) on PATH for ISO creation.

Usage:
  # 1) read-out boot CD (run first on a known-good unit; dumps profile to SD)
  rns510_flashkit.py profile-iso --swl SWL.FLI --ctest CTEST.OUT -o profile.iso

  # 2) prepare-disk boot CD (+ SD tree from a map source dir)
  rns510_flashkit.py prepare-iso --swl SWL.FLI -o prepare.iso \
      [--fhdd FHDD6.FLI --ahdd A_HDD.FRG]         # enable SD firmware flash
  rns510_flashkit.py build-sd --maps /path/to/mapsdvd --out /media/SDCARD \
      [--fhdd FHDD6.FLI --ahdd A_HDD.FRG]
"""
import argparse, os, shutil, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"

# Generic BLSCRIPT.CFG: wildcard HW match (0x0002XXXX = any VW, 0x0005XXXX = any Skoda),
# loads SWL.FLI then reboots into SWL mode. Taken from the known-good disc structure.
BLSCRIPT = """\
[FORMAT]
 HW_INFO   = <AREA ID>.<GIID>
 LOAD    = <CUSTOMER_PRODUCT_ID>.<HW_MODULE_ID>.<HW_VERSION BEGIN>.<HW_VERSION END>
[HW_INFO]
 HW_MODULE_ID    = 01.08
 HW_VERSION      = 01.01
 CUSTOMER_PRODUCT_ID   = 01.07
[0x0002XXXX.0xXXXXXXXX.0x00000000.0xFFFFFFFF]
 BAR 0 0 640 240 0xFFFF
 TEXT 2 2 1234 0xFFFF 2 "rns510-flashkit"
 PROGRESS_BAR 50 110 590 130 1687 2884 0968 9389 9863
 LOAD_FLASH_IMAGE //cddos/SWL/SILVER_1/RNSMIDEC/SWL/SWL.FLI
 SET_BOOT_MODE 0x12
 SET_BOOT_MODE 0x12
 REBOOT
[0x0005XXXX.0xXXXXXXXX.0x00000000.0xFFFFFFFF]
 BAR 0 0 640 240 0xFFFF
 TEXT 2 2 1234 0xFFFF 2 "rns510-flashkit"
 PROGRESS_BAR 50 110 590 130 1687 2884 0968 9389 9863
 LOAD_FLASH_IMAGE //cddos/SWL/SILVER_1/RNSMIDEC/SWL/SWL.FLI
 SET_BOOT_MODE 0x12
 SET_BOOT_MODE 0x12
 REBOOT
"""

VERSION_TXT = """\
--------------------------------------------
Software Loading CD for CP2 based units
--------------------------------------------
#CD:P 0 0 0 . 0 0 0 . 0 0 0
#DATE:2026-01-01
#Project: VWRNS
#Author: rns510-flashkit
#CommentStart:
Experimental SWL CD built by rns510-flashkit. Use at your own risk.
#CommentEnd:
#VwSwIndex:0000/0000/0000/0000/0000
#CRC16:0000
"""

def _need(p, what):
    if not p or not Path(p).is_file():
        sys.exit(f"error: {what} not found: {p}")
    return Path(p)

def _iso_tool():
    for t in ("xorriso", "genisoimage", "mkisofs"):
        if shutil.which(t):
            return t
    sys.exit("error: need xorriso or genisoimage on PATH to build the ISO")

def _make_iso(root: Path, out: Path):
    tool = _iso_tool()
    out = Path(out)
    if tool == "xorriso":
        cmd = ["xorriso", "-as", "mkisofs", "-iso-level", "2", "-R", "-J",
               "-V", "RNS510FK", "-o", str(out), str(root)]
    else:
        cmd = [tool, "-iso-level", "2", "-R", "-J", "-V", "RNS510FK",
               "-o", str(out), str(root)]
    subprocess.run(cmd, check=True)
    print(f"wrote {out} ({out.stat().st_size} bytes)")

def _common_tree(root: Path, swl: Path, ctest: Path | None, dlscript: Path, wsh: list[Path]):
    # mirror the real disc tree so BLSCRIPT's //cddos/SWL/... path resolves
    (root / "SWL/SILVER_1/RNSMIDEC/SWL").mkdir(parents=True)
    shutil.copy(swl, root / "SWL/SILVER_1/RNSMIDEC/SWL/SWL.FLI")
    cfg = root / "HDD/HDD_20GB/RNSMIDEC/CONFIG"
    cfg.mkdir(parents=True)
    shutil.copy(dlscript, cfg / "DLSCRIPT.TXT")
    wa = root / "WA"; wa.mkdir()
    for w in wsh:
        shutil.copy(w, wa / w.name)
    if ctest:
        shutil.copy(ctest, wa / "CTEST.OUT")
    (root / "BLSCRIPT.CFG").write_text(BLSCRIPT)
    (root / "VERSION.TXT").write_text(VERSION_TXT)
    (root / "CRC.16").write_text("0000")  # advisory only; loader warns but proceeds

def cmd_profile_iso(a):
    swl = _need(a.swl, "SWL.FLI")
    ctest = _need(a.ctest, "CTEST.OUT") if a.ctest else None
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "cd"; root.mkdir()
        _common_tree(root, swl, ctest,
                     SCRIPTS / "profile/DLSCRIPT.TXT",
                     [SCRIPTS / "profile/DUMP.WSH"])
        _make_iso(root, a.out)

def cmd_prepare_iso(a):
    swl = _need(a.swl, "SWL.FLI")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "cd"; root.mkdir()
        _common_tree(root, swl, None,
                     SCRIPTS / "prepare/DLSCRIPT.TXT",
                     [SCRIPTS / "prepare/COPYDATA.WSH"])
        _make_iso(root, a.out)
    if a.fhdd or a.ahdd:
        print("note: firmware flash lines are commented out in prepare/DLSCRIPT.TXT; "
              "enable them only after LOAD_FIB-from-/sda is confirmed on hardware.")

def cmd_build_sd(a):
    maps = _need_dir(a.maps, "maps source dir")
    out = Path(a.out)
    if not out.is_dir():
        sys.exit(f"error: SD mount point not found: {out} (mount a FAT32 SDHC <=32GB card)")
    dst = out / "mapsdvd"
    print(f"copying map tree {maps} -> {dst} ...")
    shutil.copytree(maps, dst, dirs_exist_ok=True)
    if a.fhdd or a.ahdd:
        fw = out / "fw"; fw.mkdir(exist_ok=True)
        if a.fhdd: shutil.copy(_need(a.fhdd, "FHDD6.FLI"), fw / "FHDD6.FLI")
        if a.ahdd: shutil.copy(_need(a.ahdd, "A_HDD.FRG"), fw / "A_HDD.FRG")
        print(f"staged firmware in {fw} (sizes must match the DLSCRIPT exactly)")
    print("SD tree ready. Card must be FAT32, SDHC, <=32 GB for C8/C9 hardware.")

def _need_dir(p, what):
    if not p or not Path(p).is_dir():
        sys.exit(f"error: {what} not found: {p}")
    return Path(p)

def main():
    ap = argparse.ArgumentParser(description="rns510-flashkit PC builder (experimental)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("profile-iso"); p.add_argument("--swl", required=True)
    p.add_argument("--ctest"); p.add_argument("-o", "--out", default="profile.iso")
    p.set_defaults(fn=cmd_profile_iso)
    p = sub.add_parser("prepare-iso"); p.add_argument("--swl", required=True)
    p.add_argument("--fhdd"); p.add_argument("--ahdd")
    p.add_argument("-o", "--out", default="prepare.iso"); p.set_defaults(fn=cmd_prepare_iso)
    p = sub.add_parser("build-sd"); p.add_argument("--maps", required=True)
    p.add_argument("--out", required=True); p.add_argument("--fhdd"); p.add_argument("--ahdd")
    p.set_defaults(fn=cmd_build_sd)
    a = ap.parse_args(); a.fn(a)

if __name__ == "__main__":
    main()
