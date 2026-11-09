# 3810 (noru) vs 5238 — firmware comparison + deep dig

Source: a josi "no-Russian" 3810 repack. VERSION.TXT: CD P005.157.301, 2010-11-26,
Steckbrief `C_EU_10.342_t1` C3/C4A/C5C/C6/C10, VwSwIndex 3810, author RoNe, CRC16 797b.

## Same platform, same architecture
- Disc tree identical shape: APPS/FHDD6.FLI + A_HDD.FRG, HOST, HDD, SWL, RADIO, MPEG,
  VUCI, SPEECH, WA, INFO.
- `SWL.FLI` is the same wrapper (`AA55AA55`) with a zlib stream at offset 0x21 →
  11.1 MB loader. App image `FHDD6.FLI` = 82.8 MB (vs 5238's 85.6 MB) — older/smaller.
  Same Arriba/navicore + Jeode Java + CP2 OSD; ADAS/VAdas/ElectronicHorizon
  subsystems already present (predate 5238).

## SD-flash route works on 3810 too (key result)
The 3810 loader has the full SD-source capability, same as 5238: `DRV_SDCARD_*`,
`dlsrcAddSdServiceListener`, `dlsrcSetSWLPath`, `dlsrcMultiVerifyHDD`,
`hdTermFormat`/`hdTermConfigurePartition`, `/sda`, "searching for SWL Image" / "Valid
SWL Image found". So the CD-boot + SD-payload approach is a platform feature since at
least 2010, not specific to 5238.

## Differences that matter for flashing
| | 3810 | 5238 |
|---|---|---|
| Partition recipe | `MULTI_VERIFY_HDD 3 3 50 2 25 2 25` (FS 3/2/**2**) | `… 3 50 2 25 3 25` (FS 3/2/**3**) |
| Coding: Testmode (0x21) | **set** | set |
| Coding: VIM 300 km/h (0x0B3A) | **NOT set** | set (modified disc) |
| App image size | 82.8 MB | 85.6 MB |
| BLSCRIPT HW match | `0x0002XXXX`/`0x0005XXXX`/`0x0006XXXX` wildcard | same |

- The POI partition's FS type changed 3810(2) → 5238(3): a prepare disc must match the
  target firmware generation.
- 3810 enables Testmode but **not** the video-in-motion unlock; 5238-modified enables
  both. (So VIM is a per-disc choice, not inherent to the firmware.)
- 3810 is a useful 3xxx (3-partition) reference and a forum-proven blank-disk
  formatter, but it is a josi repack, not pure VW stock. Despite the "noru" label, the
  RU language pack is still on the disc — "no Russian" refers to the install DLSCRIPT's
  language selection, not the disc contents.

## Deep dig — embedded USB-network diagnostic server

The app image contains a full developer **diagnostic/control web server**, reachable
over **USB networking (RNDIS)** — no need to open the unit for serial pins.

- **USB RNDIS network stack:** `DRV_RNDIS_RunUp/RunDown/SetIpAddr`,
  `RNDIS_ShowIpAddr`, `rndisConfigSet`, static + DHCP. The unit can present itself as a
  USB ethernet adapter (IPs referenced: **192.168.2.1 / 192.168.2.2**).
- **Native HTTP daemon** (`OslibHttpServer_c`): socket → bind → listen → `accept()` →
  **`httpAccessCheck(sockaddr_in)`** → "access allowed. Incoming connection from:
  %s:%u" or "HTTPD: access not allowed for: %s". Gated by `DevAccessCheck()` / an
  `@_devmode` flag.
- **Java servlet UI** on `:8081` (`HTMLForm`, `PageFrame`, `RequestDispatcher`,
  `SpeechServlet`, `UtilityServlet`, …), alongside the native server.
- **Telnet console** (`telnetdStart`/`usrTelnetdStart`, `riocsl00: telnet console`) →
  the VxWorks `tShell` over TCP, in addition to the serial tShell.

**Diagnostic/control pages served** (JS handlers): `setLatLong` (inject GPS position),
`setuserdefineddbpath` (point the nav engine at an arbitrary map DB path),
`vp/vs/vl_show_state` (Vehicle Positioning / SimInput / Log Player — feed or replay
position), `wg_show_state` (Waypoint Generator), `rg_repeat_voice`, `speakSentence`
(make the TTS speak arbitrary text), `sds_show_state` (Sirius data services), map pan
(`scrollPage`/`mjLeft`/`posTop`), `onClamp15` (ignition clamp), plus VxWorks
stack/heap/task dumps. 19 diagnostic pages in total — a full developer control panel
over the live nav/media stack.

**Why it matters:** if `DevAccessCheck`/`httpAccessCheck` can be satisfied (and
devmode enabled), a USB cable gives a web UI to trace/dump/control the live nav+media
stack and inject simulated GPS — far richer and more accessible than the serial
console. **Open question:** whether a *production* kernel starts telnetd/httpd and what
`httpAccessCheck` allows. A separate **"full development kernel"** (`SDC_DB_DEVF`)
exists, and the HTTP/telnet features appear tied to it / `_devmode`. The exact access
rule needs the decompiled `httpAccessCheck` — which sits just past the ~9 MB boundary
where the recovered load base stops mapping (the wiki's documented dead zone), so its
string refs don't resolve without a second load base for the >9 MB region (unrecovered).

Note: the **SWL loader** (`SWL.FLI` decompressed) *does* have a clean recoverable base
(validated against its own format strings), so the loader's flash/format/SD logic is
fully decompilable — the HDD-format function writes a custom partition magic
(`0x4b24bcf6`/`bd9e`/`be06`) the unit must self-write (PC tools can't reproduce it),
and `dlsrcRegisterSources` registers the Dvd/Sd/HDD event listeners and sets
`currentSourcePath` — the multi-source CD/SD/HDD architecture, confirmed.

## Embedded coding definition file (CAF) — the coding mod reference
The firmware embeds the manufacturer's **CAF coding files** (`SysCfgCstCodingFile.xml`,
104 `<CAF>` blocks for platform variants) — structured XML mapping each coding byte →
bit-mask → function, with German descriptions. The vehicle "long coding" byte map:
- **Byte 0** Radiokonfiguration 1: CD-Changer, AUX-In diagnosis, Parkhilfe (PDC)
- **Byte 1** Power Amplifier / SoundSystemCorrection: `NO_DSP` / `BOOSTER_DSP4` / Dynaudio
- **Byte 2** passive speaker channels (open-load monitoring)
- **Byte 3** Radiokonfiguration 2: Microphone diagnosis, Sirius RegionalCode
- **Byte 4** tweeter open-load detection
- **Byte 5** vehicle-specific frequency response
- **Byte 6** Radiokonfiguration 3: **GALA** (speed-dependent volume), **DAB Country**
- **Byte 7–8** Navigation config 1/2

This is the authoritative source for coding mods (sound-system type, GALA, DAB, PDC,
AUX, Sirius region) — and it ties the on-unit coding to the VCDS "long coding" that
tools like SetConfig expose (see `setconfig-analysis.md`).
