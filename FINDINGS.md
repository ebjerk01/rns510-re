# RNS-510 firmware RE — findings

Target: `FHDD6.FLI` from the 5238 "modified" SWL disc (the unit is 1T0035680C / HW H42 / SW 2720).
sha256 of FHDD6.FLI: `9807b06be3174ec797e604898970f59c78384bf9b0e8b999a9e71fae54f99624`.
Goal: flaws, performance, mods. This builds on the krcenov RE wiki (<https://github.com/krcenov/RNS510-Map-Viewer/wiki>).

## Platform recap

- MPC5200 (PPC603e, ~400 MHz), VxWorks 5.5, gcc-2.96. See `README.md`.
- `FHDD6.FLI` = 3 regions: **0–24 MB** native PPC (navicore), **24–76 MB** Java classes, **76–85.6 MB** VxWorks kernel/BSP.
- Verified load base (krcenov): `VA = file_offset + 0xf688dcf4`, holds only for the ~1.2–9 MB code-dense sub-range.
- The Ghidra project: a Ghidra project — the 1.2–9 MB region imported raw PPC BE at base `0xf69b2c74`.

---

## The real mod surface (ranked by effort/risk)

### 1. Vehicle coding — plaintext, lowest risk, highest payoff
The SWL disc's own `WA/*.WSH` scripts are plaintext and set the unit's coding. No binary patching needed. Confirmed registers:

**Coding array at register `0x400` (one byte per offset, width 1):**
| Offset | Meaning | Values |
|---|---|---|
| 1 | manufacturer | 0x02 = VW, 0x05 = Skoda |
| 2 | HDD active | 0/1 |
| 5 | Tuner "RUDI" active | 1 |
| 6 | DAB active | 0/1 |
| 7 | SDARS (Sirius) active | 0 in EU |
| 8 | MPEG active | 0/1 |
| 9–15 | reserved/unused on these discs | 0 |

**Register writes (same on all EU variants):**
| Register | Value | Meaning |
|---|---|---|
| `0xa91` | 0 (w2) | "Delete Presets" |
| `0x21` | 01 | **Testmode: Active** |
| `0x0B3A` | 012C (300 dec) | **Speed limit DVD/TV: 300 km/h** — the video-in-motion (VIM) safety-lockout override |
| `0x0a0a` | 01 | (Skoda only) "Big VW Splashscreen in NAND: Not Active" — per-brand splash selector |

This "modified" josi disc already enables Testmode and the 300 km/h VIM unlock. Coding is also reachable live over the serial console via `CTEST.OUT`'s `SetCoding`/`SetRegDataHex` (see the wiki's serial-console page), so these can be changed on a running unit without reflashing.

### 2. Startup logo / splash — simple format, low risk
`logo.fli`, RGB555, with a CRC16 that Remko Weijnen documented. Tools exist (RNS 510 Editor). A splash swap is a known, safe mod. The brand splash is also toggled by coding register `0x0a0a`.

### 3. SWL / flash scripts — plaintext, medium risk
Everything that drives a flash is plaintext and only CRC16-protected (see flaws):
- `BLSCRIPT.CFG` (hardware match), `CONFIG/DLSCRIPT.TXT` (per-variant flash program), `WA/*.WSH` (VxWorks shell).
- You can change what gets flashed, which language, which coding — this is how all community firmware is built.
- The flash command language (`LOAD_FIB`, `INSTALL_FRAGMENT`, `LOAD_ECU_BLOCK`, `COMPARE_REG_ID`, `RUN_SHELL_SCRIPT`) is documented in the krcenov wiki: <https://github.com/krcenov/RNS510-Map-Viewer/wiki/SWL-Disc-Boot-Chain-and-Build-System>.

### 4. POI data via EDB — supported, no risk
`vdo.nav.api.edb.*` is a JDBC-like client to an embedded SQLite engine. Custom POI `.db3` files under `EDB/POI/` are a supported extension (name/lat/lon only; no road geometry). Not UI modding, but a real data mod.

### 5. UI state machine — found, partially open (native lead)
Embedded in the native region at file offset **0x1041fe–0x125ee4** (~138 KB) is a statechart model (EMF/GMF style: `<Transition>`, `idref`, `source`/`target`), extracted for analysis.
- Guard nodes: `allow_context_media`, `allow_context_setup`, `allow_context_testmode`, `allow_context_tone`.
- Action transitions: `jlaxPerformAction`, `jlaxPerformExtendedAction` with `fp0..fp4` params.
- This is the most promising lead for unlocking hidden menus/contexts **without** touching the romized Java — the guards appear to be data in this model, not compiled bytecode. Needs the native code that interprets `allow_context_*` (Ghidra pass) to confirm whether flipping a guard is enough.

### WALLED: Java UI (new buttons/screens)
The touchscreen UI is Java on the Jeode EVM, stored as "romized" (pre-linked) class bodies. Standard decompilers only recover trivial interface classes. Per the wiki this is a tested wall — new buttons/screens are **not** achievable with current public tooling. Do not promise UI mods.

---

## Flaws / weaknesses

1. **No secure boot / no signed firmware.** SWL discs are integrity-checked by **CRC16 only** (`CdTreeBuilder`, `#CRC16:` in VERSION.TXT, `CRC.16` tree). There is no cryptographic signature. Anyone can build and flash modified firmware — the root cause that makes every community mod possible, and a genuine security weakness (a malicious disc is indistinguishable from a genuine one to the unit).
2. **Safety lockout is coding-overridable.** The "no video while driving" limit is just register `0x0B3A`; setting 300 km/h disables it. Plaintext, no authentication beyond physical/serial access.
3. **Theft-protection PIN is brute-forceable.** `TpPvVerifyPin` accepts a PIN in the range **0–1999** (2000 values) over the 115200-baud serial console with no rate limiting found. Community tools already brute-force it. (krcenov, Theft-Protection page.)
4. **Testmode enabled by default on modified discs.** `0x21=01` leaves engineering/test screens reachable.
5. **Embedded data leaks.** The image contains an internal confidentiality/"trade secrets" email footer and internal engineer initials (RoNe, MaRu) — minor info leak, not exploitable.

---

## Performance — honest assessment

On a 2010 MPC5200 you cannot meaningfully speed up the nav engine by patching native code: you would have to rebuild and reflash a romized Jeode image, which is not practical and is high-risk. The real, achievable wins for an owner are:
- **SSD swap** (in progress) — removes HDD seek latency, the single biggest real-world responsiveness gain.
- **Coding off unused subsystems** (DAB/SDARS/MPEG/TV when not fitted) so the UI stops polling them.
- **Firmware version** — 2660+ advertises "faster startup"; 5238 is the newest for the C-class hardware.
- Binary-patch perf tuning = academic. Note it, don't chase it.

---

## Native pass (Ghidra) — in progress

a Ghidra project, 1.2–9 MB region, base `0xf69b2c74`. Once analysis is saved, pull:
- the function that reads `allow_context_*` (does flipping a guard unlock a context?),
- the CRC16 / SWL-media validation path (confirms #1),
- startup/bootMgr sequencing (any low-risk perf or logging wins).

---

## Addendum (parallel analysis while native pass ran)

### Full UI screen list — 86 screens
Enumerated from the Java region (`Menu_*Rules`/`MenuNet_*Rules`), matches the wiki's count exactly; listed in `artifacts/ui_screens_86.txt`. Hidden/engineering screens present and real: `MenuNet_TESTMODE`, `MenuNet_TESTMODE_SYSTEM`, `MenuNet_SERVICE`, `MenuNet_CODE_CHECK`, `Menu_TESTMODE_DAB_MONITOR_MAIN`, `Menu_SYS_CODE_INPUT`, `Menu_SYS_CODE_SYSTEM_SAFE`. These tie to coding `0x21=Testmode Active` — the screens exist in this build, coding gates reachability.

### Correction: the 0x1041fe statechart is the BOOT MANAGER, not the UI menu guards
It is the bmgr (boot-manager) lifecycle model: SDC (shutdown-consumer) run-up/run-down/shutdown ordering — `bmgrSetState`, `bmgrPerformSdcRu/Rd/Sd`, `bmgrTimer`, `informNaviCoreAboutRundownAndGiveChanceToSaveParameters`. The `allow_context_{media,setup,testmode,tone}` nodes gate contexts *during the lifecycle*, not menu entry. This is the **startup/shutdown sequencer**.

### Performance lead (honest): named boot delays
The bmgr model contains deliberate delay timers:
`workaround_delay_faster_radio`, `delay_instrument_cluster`, `delay_before_reset` (≈15), `delay_resume_copy`, `delay_for_symptoms_output`, `delay_reset_for_monitor_output`, `init MMP timeout` (≈3), `store MMP timeout`.
`workaround_delay_faster_radio` is a deliberately inserted delay in the radio-startup path — the kind of thing that, if tunable, would speed perceived boot. **But** the numeric durations are not co-located with the names in the model (they live in the compiled statechart interpreter / separate value nodes), so this is **not** a simple hex edit. It's a real lead, not a ready mod. Confirming it needs the native interpreter code (Ghidra).

### USER.CFG is disc-build config, not a runtime lever
`INFO/USER.CFG` drives CdTreeBuilder when the disc is built (`HARDWARE_C6/C10/C12=1`, `PROJMAP_*`, `FACTORY_CD=0`, `ONE_FIB=1`). It does not toggle features on the unit. Runtime feature control is the coding registers (section 1), not this file.
