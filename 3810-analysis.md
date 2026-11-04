# Firmware 3810 — analysis, and comparison with 5238


Source: `3810a_noru.rar`, a josi "no-Russian" repack.
VERSION.TXT: CD P005.157.301, 2010-11-26, Steckbrief C_EU_10.342_t1 C3/C4A/C5C/C6/C10,
VwSwIndex 3810, author RoNe, CRC16 797b.

## Same platform, same architecture
- Disc tree identical shape: APPS/FHDD6.FLI + A_HDD.FRG, HOST, HDD, SWL, RADIO, MPEG, VUCI, SPEECH, WA, INFO.
- `SWL.FLI` is the same wrapper (`AA55AA55`) with a zlib stream at offset 0x21 → 11.1 MB loader (decompressed from the SWL.FLI zlib stream).
- App image `FHDD6.FLI` = 82.8 MB (vs 5238's 85.6 MB) — older/smaller. Same Arriba/navicore + Jeode Java + CP2 OSD; ADAS/VAdas/ElectronicHorizon subsystems already present (predate 5238).

## SD-flash route works on 3810 too (key result)
The 3810 loader has the full SD-source capability, same as 5238:
`DRV_SDCARD_*` (137), `dlsrcAddSdServiceListener` (5), `dlsrcSetSWLPath` (3),
`dlsrcMultiVerifyHDD` (15), `hdTermFormat`/`hdTermConfigurePartition`, `/sda`,
"searching for SWL Image" / "Valid SWL Image found". So the CD-boot + SD-payload
approach is a platform feature since at least 2010, not specific to 5238.

## Differences that matter for flashing
| | 3810 | 5238 |
|---|---|---|
| Partition recipe | `MULTI_VERIFY_HDD 3 3 50 2 25 2 25` (FS 3/2/**2**) | `... 3 50 2 25 3 25` (FS 3/2/**3**) |
| Coding: Testmode (0x21) | **set** (EURPQTO/EURSKHDD) | set |
| Coding: VIM 300 km/h (0x0B3A) | **NOT set** | set (modified disc) |
| App image size | 82.8 MB | 85.6 MB |
| BLSCRIPT HW match | `0x0002XXXX`/`0x0005XXXX`/`0x0006XXXX` wildcard | same |

- The POI partition's FS type changed 3810(2) → 5238(3): a prepare disc must match the target firmware.
- 3810 enables Testmode but not the video-in-motion unlock; 5238-modified enables both.
- 3810 is below the 680C's max (5269) and above nothing special — it's useful as a 3xxx (3-partition) reference and a forum-proven blank-disk formatter, but it's a josi repack, not pure VW stock.

## Note
Despite the "noru" label, 15 LANG_*.FRG (incl. RU) are on the disc — the "no Russian"
likely refers to the install DLSCRIPT's language selection, not the disc contents.

## Deep dig (2026-11-04): embedded USB-network diagnostic server

The app image contains a full developer **diagnostic/control web server**, reachable over **USB networking (RNDIS)** — no need to open the unit for serial pins.

- **USB RNDIS network stack:** `DRV_RNDIS_RunUp/RunDown/SetIpAddr`, `RNDIS_ShowIpAddr`,
  `rndisConfigSet`, `rndisIpAddr = %s`, `GetAllLocalIPAddresses`, static+DHCP IP
  ("Can't use dynamic address without DHCP"). The unit can present itself as a USB
  ethernet adapter.
- **Native HTTP daemon** (`OslibHttpServer_c`): creates socket → bind → listen →
  `accept()` → **`httpAccessCheck(sockaddr_in)`** → logs "access allowed. Incoming
  connection from: %s:%u" or "HTTPD: access not allowed for: %s". Gated by
  `DevAccessCheck()` / an `@_devmode` flag.
- **Java servlet UI** too: references `http://localhost:8081/servlet/resources/logo.gif`,
  `.../g_mch_w_p_012_k.jpg` — a servlet-based web interface alongside the native one.
- **Telnet console** (`java:riocsl00: telnet console`) in addition to the serial tShell.

**Diagnostic/control pages served** (from `<b>` headings + hrefs): Waypoint Generator
(ShowState/pause/resume/addwaypoint/setalgorithm), Route Guidance Trace, ARRNAVI
messaging/startup/task info, **Vehicle Positioning SimInput + Log Player** (inject/replay
GPS), Small Adas, Scroll/Zoom/Rotate pad, Sentence/Token lists, **Sirius Data Services
control panel**, Data Services Copy Task control panel, VxWorks Stack/heap/task dumps
(`oslib_dumpTaskInfoHTTP`), and event simulation endpoints (`/ArribaStartup/.../simDVDEjectReq`,
`/Task/.../GENERATE_STACK_TRACE`, `/NaviTrace`, `/MessageTrace`).

**Why this matters:** if `DevAccessCheck`/`httpAccessCheck` can be satisfied (and devmode
enabled), a USB cable gives a web UI to trace/dump/control the live nav+media stack and
inject simulated GPS — a far richer, far more accessible interface than the serial console.
Open question: the exact access rule (which client IPs pass) and the devmode enable
condition — needs the decompiled `httpAccessCheck`/`DevAccessCheck`. NOTE: that code sits just past the ~9MB boundary where the recovered load base stops mapping (the wiki`s documented dead zone), so Ghidra cannot resolve its string refs — decompiling it needs a second load base for the >9MB region (unrecovered). (The 3810 native
region).

## Embedded coding definition file (CAF) — the coding mod reference
The firmware embeds the manufacturer's **CAF coding files** (`SysCfgCstCodingFile.xml`,
51 refs, 104 `<CAF>` blocks for platform variants) — structured XML mapping each coding
byte → bit-mask → function, with German descriptions. Extracted from the firmware image.
Byte map (the vehicle "long coding"):
- **Byte 0** Radiokonfiguration 1: CD-Changer (CDC), AUX-In diagnosis, Parkhilfe (PDC)
- **Byte 1** Power Amplifier / SoundSystemCorrection: `NO_DSP` / `BOOSTER_DSP4` / `Dynaudio-Soundsystem`
- **Byte 2** passive speaker channels (open-load monitoring)
- **Byte 3** Radiokonfiguration 2: Microphone diagnosis, Sirius RegionalCode (US 0x00, Canada 0x02/0x03)
- **Byte 4** tweeter open-load detection
- **Byte 5** vehicle-specific frequency response
- **Byte 6** Radiokonfiguration 3: **GALA** (speed-dependent volume), **DAB Country**
- **Byte 7–8** Navigation config 1/2
This is the authoritative source for coding mods (sound system type, GALA, DAB, PDC, AUX, Sirius region).

## USB-net access details
- RNDIS/USB-net IPs referenced: **192.168.2.1 / 192.168.2.2** (likely unit↔host), with
  `RNDIS_KEEPALIVE_MSG`, static + DHCP, netmask-from-boot-field.
- A **"full development kernel"** variant exists (`SDC_DB_DEVF`, "Development System"); the
  HTTP/telnet dev features are tied to that/`_devmode` — likely OFF on a production kernel,
  which is why `httpAccessCheck`/`DevAccessCheck` matters (whether a production unit answers).
- Web UI served by BOTH a native `OslibHttpServer` and a Java **servlet container**
  (`HTMLForm`, `PageFrame`, `RequestDispatcher`, `SpeechServlet`, `UtilityServlet`, …) on `:8081`.

## Access vectors summary (USB → unit)
- **RNDIS USB network**: unit presents a USB ethernet adapter (likely 192.168.2.1/.2).
- Then potentially reachable over that network:
  - **telnet daemon** (`telnetdStart`/`usrTelnetdStart`, `riocsl00: telnet console`) → the VxWorks `tShell` (full shell) over TCP.
  - **native HTTP server** (`OslibHttpServer`) + **Java servlet UI** (`:8081`) → the diagnostic/control pages.
- All gated by `_devmode`/`DevAccessCheck`/`httpAccessCheck`, and there is a separate
  **"full development kernel"** (`SDC_DB_DEVF`). Open question (being decompiled): whether a
  production kernel starts telnetd/httpd and what `httpAccessCheck` allows. If they're dev-kernel-only,
  enabling them on a production unit would need a coding/boot change or flashing a dev kernel.
- ServiceMode screens (`SERVICEMODE_AM/SDARS`, `ServiceModeTuner`) are the coded service menus — a lower-tier, already-reachable diagnostic path.

## RNDIS/USB startup + more
- `DRV_RNDIS_RunUp` appears as a **bmgr lifecycle `<Action>`** — USB networking is wired into the
  boot-manager startup actions (USB device-mode: `usbTargInitialize`, `FMDeviceController`,
  "device controller"). So it *can* come up during boot; whether it's triggered unconditionally
  or gated (devmode/dev-kernel/coding) is the same open question as the HTTP server — needs the
  lifecycle condition or live testing.
- A debug monitor is loadable: `bmgrLoadLib (/tffs0/lib/tools/monitor2SDC.o)`.
- Base-recovery note: the FHDD6 >9 MB region does not resolve string refs at the 0xf688dcf4 base
  (no lis/addi or pointer hits for the HTTP strings), confirming it uses a different/again-unrecovered
  base. The **SWL loader** (`SWL.FLI` decompressed) DOES have a clean recoverable base: **0xfedb0000**
  (validated against its own format strings) — so the loader's flash/format/SD logic is decompilable
  (decompiled from the recovered base).
