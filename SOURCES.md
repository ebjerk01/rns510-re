# Sources & credits

Reverse-engineering notes on the VW RNS-510 (Continental/Siemens VDO, MPC5200/VxWorks)
navigation head unit. This repo contains **analysis and documentation only** — no
proprietary Continental/VW firmware binaries, no map data, and no unit-identifying data.

Analysis builds heavily on prior public work:

- **krcenov — RNS510-Map-Viewer** (GPL-3.0; wiki + tools): the deepest public RE of the
  RNS-510 firmware, map formats, boot chain, vehicle coding and serial console.
  https://github.com/krcenov/RNS510-Map-Viewer
- **Edward03YT — RNS510-Bootlogo-Toolkit** (GPL-3.0): bootlogo creation, the FLI
  container + CRC-16/XMODEM, and SWL ISO building.
  https://github.com/Edward03YT/RNS510-Bootlogo-Toolkit
- **Edward03YT — rns510-companion** (MIT): VCDS log analyzer and a firmware/hardware
  compatibility checker. https://github.com/Edward03YT/rns510-companion
- **SlashGordon — rns510-code-finder** (MIT): serial PIN brute-forcer.
  https://github.com/SlashGordon/rns510-code-finder
### Related projects — the CAN / BAP side

These reverse-engineer the on-wire CAN/BAP channel to the RNS-510 (the counterpart to
this repo's firmware-side RE); the BAP CAN IDs in `can-bus-findings.md` come from them:

- **majonezz — rns510-tv-input**: a Linux SocketCAN daemon emulating a MOST/BAP
  TV-tuner to the RNS-510 (BAP IDs 0x6D3/0x6C7/0x602, ignition 0x575, radio 0x661).
  https://github.com/majonezz/rns510-tv-input
- **AugustoS97 — CanBus-Radio-VAG**: waking a VAG radio on a bench; confirms the
  0x575 ignition frame and shares an infotainment DBC.
  https://github.com/AugustoS97/CanBus-Radio-VAG
- **DSchndr — mfd2plusplus**: MFD2 (RNS-510's sibling) CarPlay + custom
  instrument-cluster messages. https://github.com/DSchndr/mfd2plusplus
- **ValeraBat — VW_CDC_ESP32BT1036C**: ESP32 CD-changer/Bluetooth emulator over the
  radio bus. https://github.com/ValeraBat/VW_CDC_ESP32BT1036C

### Other references

- **my-gti.com** — firmware repository and the HW↔SW (firmware) versions table.
- **paulroberts69.wordpress.com** — SSD swap and firmware/maps upgrade write-ups.
- **altechnative.net** — RNS-510 firmware/maps update guide.
- **Remko Weijnen** — startup-logo format and VERSION.TXT CRC16.

## Relationship to the other repos & licensing of the tools here

The tools in `tools/` (the serial coding/PIN client and the compatibility checker) are
**clean-room**: they are implemented from this project's own reverse-engineering and
from publicly-known facts (the serial command names, the HW↔firmware generation map),
**not** copied or derived from the repos above. No GPL-3.0 code from krcenov or the
Bootlogo-Toolkit is included, so this repository can remain MIT-licensed. The tools
cover deliberately different ground from the prior repos (serial coding + the
documented PIN mechanism; firmware-generation compatibility) and cite them as prior art.

Firmware images, the map tool, photos and the unit serial are deliberately **excluded**
(copyright + privacy). This repo is interoperability/repair research on hardware the
author owns.
