# RNS-510 CAN / vehicle-data findings

## Architecture
The RNS-510 does not read raw vehicle CAN directly in its app. Its **ST10 gateway**
(`VUCI/.../GATEWAY.FLI`, 884 KB, C166) bridges the car's **comfort/infotainment CAN**
to **MOST/BAP** (VW's Bedien-/Anzeige-Protokoll), and the app (`FHDD6.FLI`) consumes
decoded signals over MOST. Per-platform routing tables: `PQTABLE.FLI` (Golf/Passat PQ),
`SKTABLE.FLI` (Skoda), `TOTABLE.FLI` (Touareg) — all K2L GmbH format, 8 KB each.

## PQTABLE.FLI structure (partial decode)
K2L GmbH table, header "K2L GmbHVer.1.4344.2A.09.00 ... 01.43". After the header,
**93 fixed records** (24-byte stride, each terminated by `CD CD`), fields:
`<paramID u16> 00 00 00 <subIdx u16> <regAddrA u16> <regAddrB u16> <len*256 u16> <offset u16> FFFF`
- paramID (col0): ordered IDs 0x02c1…0x0531 (MOST/BAP parameter IDs)
- regAddrA (col5): internal register/parameter addresses incl. **0x091C** (the language register, confirmed elsewhere)
- len (col7): high byte = data length (3/5/6/7/8)
So PQTABLE maps **MOST/BAP parameter ID → internal register + length**, i.e. the MOST
side — NOT raw CAN IDs. The raw CAN message IDs are hardcoded in the ST10 gateway code
(would need C166 disassembly via `hn/c166-dis`, as krcenov used for the theft-protection).

## Vehicle signals the unit actually uses (from GATEWAY.FLI strings)
Comfort/infotainment only — NO powertrain data:
- **CarSpeed** (GALA volume, video-while-driving lockout)
- **Clamp 15 / 58d** (`CLAMP_STATUS`, `Cl58d_w_f`, `CANDimmung`, `CL_LAST_DIMMUNG`) — ignition + dash dimming
- **Reverse gear** (`reverseGear3`) — RVC trigger
- **PDC** (`CL_CODING_PARK_DISTANCE_CONTROL`, `CL_PARK_CONSUMER_GRAPH`)
- **MFL** steering-wheel buttons (`CL_CODING_MFL_ONOFF`, `CodingShadow_Received_MFL_ONOFF_ID`)
- **Instrument cluster** (`CL_CODING_INSTRUMENT_CLUSTER`)
- **Illumination/TFT dimming** (`CL_CODING_ILLUMINATION_*`, `TFT_BACKLIGHT_CALIB_FACTOR`, weighting curves)
- **Fan/temperature** (`Diag_Get_ExternalFanSpeed`, `CTRL_OverTemp`, `BACK_TEMP_OVERRIDE`)
- **Audio config** (`CL_CODING_AUX_IN`, `CL_CODING_DSP`, `CL_CODING_BAP_AMPLIFIER`)
- **VIN/odometer** (Kombi `0x623`)

## NOT present (confirmed absent)
No boost/turbo, RPM, engine load, oil temp, coolant temp, throttle, torque — zero exact-token
hits (the "boost"/"rpm" string hits are `BOOSTER_DSP4` amp coding, Java GC "boosting", and
`BMgrPMMInterfSdc`). Powertrain data is on the drivetrain CAN, behind the gateway, not reachable.

## MOST function IDs
The gateway exposes a block of MOST FBlock function IDs (~0xE15–0xE3C range, 47 values) to
the app, logged as `MOST FktId=0x%03Xh`. Mapping each to a handler needs the ST10 disassembly.

## To get a real CAN DBC
Disassemble `GATEWAY.FLI` (ST10/C166) with `hn/c166-dis` and trace the CAN RX handlers — the
only path to raw CAN IDs + signal bit positions. Not done (large effort); noted as next step.
