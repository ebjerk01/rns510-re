# RNS-510 coding reference (consolidated, cross-generation)

Three distinct coding systems live in the unit. This consolidates them from the CAF
definition file, the SWL `.WSH` scripts, and the firmware diffs (3810 / 5238 / 5274 /
6276).

## 1. HU_CODING — the manufacturer "long coding" (CAF, address `0600h`, 10 bytes)
From the embedded `SysCfgCstCodingFile.xml` (CAF). **Stable across all four firmware
generations** (3810/5238/5274/6276 all carry the same byte map; 6276 only adds detail
to Byte 9). This is the VCDS-visible vehicle coding.

| Byte | Function (German label) | What it controls |
|---|---|---|
| 0 | Radiokonfiguration 1 | CD-Changer (CDC), AUX-In diagnosis, Parkhilfe (PDC) |
| 1 | Power Amplifier Config + Amplifier Constellation | `NO_DSP` / `BOOSTER_DSP4` / Dynaudio sound system |
| 2 | Anzahl passive Lautsprecherkanäle | passive speaker channels (open-load monitoring) |
| 3 | Radiokonfiguration 2 | Microphone diagnosis, Sirius RegionalCode |
| 4 | Open-Load Erkennung Hochtonlautsprecher | tweeter open-load detection |
| 5 | Fahrzeugspezifischer Frequenzgang | vehicle-specific frequency response |
| 6 | Radiokonfiguration 3 | **GALA** (speed-dependent volume), **DAB Country** |
| 7 | Navikonfiguration 1 | navigation config |
| 8 | Navikonfiguration 2 | navigation config |
| 9 | Additional OPS graphics | parking-sensor (OPS) graphics |

CAF format: `<Data name="HU_CODING" address="0600h" units="10">` → `<Function
name="Byte_N">` → bit masks + German comments, default `0xFF`. (This is what
`LCode.exe` and VCDS labels decode; see `setconfig-analysis.md`.)

## 2. Register coding — the `0x400` array + special registers (from the `.WSH` scripts)
Set over the serial console / SWL scripts via `SetCoding(0x400, val, offset, width)`
and `SetRegDataHex(reg, "hex", …)`. From `EURPQTO.WSH`/`ESKHDDL.WSH`/`VIM.WSH`:

**`0x400` coding array (one byte per offset):**
| Offset | Meaning | Values |
|---|---|---|
| 1 | manufacturer | 0x02 = VW, 0x05 = Skoda |
| 2 | HDD active | 0/1 |
| 5 | Tuner "RUDI" active | 1 |
| 6 | DAB active | 0/1 |
| 7 | SDARS (Sirius) active | 0 in EU |
| 8 | MPEG active | 0/1 |
| 9–15 | reserved | 0 |

**Special registers:**
| Register | Value | Meaning |
|---|---|---|
| `0x21` | 01 | **Testmode active** (engineering/test screens) |
| `0x0B3A` | 012C (300) | **Video-in-motion unlock** (speed limit DVD/TV = 300 km/h) |
| `0x0a0a` | 01 | brand splash selector (Skoda: big VW splash in NAND not active) |
| `0xa91` | 0 (w2) | Delete Presets |

(Testmode + VIM are present in both stock and "modified" delivery scripts — see
`5274-stock-vs-modified.md`.)

## 3. JReg settings coding — newer builds only (`MM_SETTINGS`)
Newer firmware (5274/6276, not 5238) adds a **registry-path coding/settings layer**
alongside the above, plus a `data/CCC_Gateway_Coding.xml`. Entries look like:
```
<codingentry JRegRootName="TLAUser" JRegPath="/MM_SETTINGS/AudioSettingsService/ENTDYN" JRegKey="dynamicCompressionCurve">
<codingentry JRegRootName="TLAUser" JRegPath="/app/TMCSetting"        JRegKey="FM-TMC">
<codingentry JRegRootName="system"  JRegPath="/system/uiset/map/color" JRegKey="currentNight">
```
Roots `TLAUser` / `system`; paths under `/MM_SETTINGS/...`, `/system/uiset/...`. (See
`fhdd6-version-diff.md`.) Not reachable on a 680C since its firmware ceiling is ~5269.

## 4. Gateway coding items (`CL_CODING_*`, in GATEWAY.FLI)
Stable across generations (unchanged 5238→6276). The ST10 gateway's own coding:
illumination dimming/weighting curve (`CL_CODING_ILLUMINATION_*`), instrument cluster
(`CL_CODING_INSTRUMENT_CLUSTER`), MFL steering buttons, PDC, AUX, DSP, BAP amplifier.
See `gateway-st10-findings.md`.

## Summary — what's stable vs new
- **Stable across all generations:** HU_CODING 10-byte long coding, the `0x400`
  register array + special registers, the `CL_CODING_*` gateway items.
- **New in 5274/6276:** the JReg `MM_SETTINGS` settings layer + `CCC_Gateway_Coding.xml`.
- Practical mod surface on a 680C (≤5269): HU_CODING + the register/special coding —
  all plaintext and reachable over serial / SWL scripts, no binary patching.
