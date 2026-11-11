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

## Raw BAP CAN IDs — known from community work
The on-wire CAN IDs for the RNS-510's BAP/MOST channel are already reverse-engineered
in the community and corroborate the firmware-side findings above. From majonezz's
`rns510-tv-input` (a Linux SocketCAN daemon that emulates a MOST/BAP TV-tuner to the
unit) and AugustoS97's `CanBus-Radio-VAG`:

| CAN ID | Direction | Meaning |
|---|---|---|
| `0x6D3` | → unit | BAP messages to the radio (TX; segmented into 8-byte frames) |
| `0x6C7` | ← unit | BAP requests from the radio (RX) |
| `0x602` | → unit | heartbeat (8 zero bytes, ~1 Hz) |
| `0x575` | → unit | **ignition / wake** (infotainment+comfort bus; confirmed by two sources) |
| `0x661` | → unit | radio on/off |

Buses: **infotainment 100 kbps, comfort/convenience 100 kbps, drivetrain 500 kbps**.
`0x575` on the infotainment/comfort bus is the key to **waking the radio on a bench**.
The BAP FBlock function IDs seen on that channel (FBLOCK_AVAILABILITY 0x02,
TUNE_TO_HYBRID 0x11, SOURCE 0x15, TUNER_STATUS 0x1F, TTCONTROL 0x21, COLOR 0x24, …)
match the gateway's `BAP FktId` / `MOST FktId` map. So the firmware-internal FBlock IDs
(above) and these on-wire CAN IDs are two views of the same channel.

To extend to the full comfort-signal CAN map (speed/clamp/illumination bit positions),
either sniff the car or disassemble `GATEWAY.FLI` (ST10/C166) with `hn/c166-dis` and
trace the CAN RX handlers. (See SOURCES for the community references.)
