# ST10 gateway (GATEWAY.FLI) — findings

Source: `VUCI/B101/RNSMIDEC/PROG/GATEWAY.FLI` (884,736 B, identical in 3810 and 5238).
`aa55aa55`-wrapped, **uncompressed** C166/ST10 image (entropy 6.67, no zlib). The
ST10F276 is a C166-family core.

## Architecture
- The gateway bridges the car's **comfort/infotainment CAN** to the app side
  (MOST/BAP). The image is MOST/BAP-heavy: `BAP_*`, `MOST FktId=%03Xh`, `BAPLsgId`,
  `BAP_StatusAll_Reply_To_SHadow`, device/FBlock/function routing.
- CAN is handled through an inter-processor path to a **VUC**: `ipcVuC_CanRxHandler`,
  `ipcVuC_CmsRxHandler`, `ipcVuC_AmsTxHandler`, over IPC **ring buffers**
  (`++++++++ipcVuc+++++++ RingBuffer %d re-initialized`). `CAN_Task`, wake-up events
  (`CAN_Trigger_Consumer_CB: Radio_On/Off wake up; event %04X`), `CanLost`/`CanRecovery`.

## Comfort-CAN signals the gateway uses (confirms can-bus-findings.md)
`CarSpeed` ("Received Msg CarSpeed valid"), `Clamp15`/`Clamp30`/`Clamp58d`
(`Cl58d_w_f`, `Override ClampR_Off_Timer`), illumination/dimming
(`CL_CODING_ILLUMINATION_DIMMING_SETTINGS`, `..._WEIGHTING_CURVE_CAN`), instrument
cluster (`CL_CODING_INSTRUMENT_CLUSTER`), TPMS (`CL_TPMS_LOST_CAN_MESSAGES`).
Comfort signals only — **no powertrain data** (no boost/RPM/load), consistent with
earlier findings.

## DTC / fault table (fault name, DTC code, sub-byte)
| Fault | DTC | sub |
|---|---|---|
| Clamp30 Undervoltage Warning | 0x01BE | 0x02 |
| Clamp30 Overvoltage Warning | 0x01BF | 0x01 |
| Clamp30 Voltage Critical | 0x0214 | — |
| Temperature | 0x01C5 | 0x01 |
| Keyboard | 0x08C4 | 0x00 |
| CANBus OFF | 0x0519 / 0x0538 | 0x0E |
("CANBus OFF 0x0519 suppressed due to voltage" — the gateway suppresses the CAN-off
DTC during undervoltage.)

## Theft protection (THP) — the real state machine
Persisted in EEPROM as `THP: EEPROM: CS:.. LS:.. BT:.. UT:.. FUL:../.. PUL:../..
IP:../..` — Current State, Last State, Blocking Timer, Unlock Timer, Failed-Unlock
count/limit, Pin-Unlock count/limit, Input-Pin count/limit. `THP: Cnt=%d, Limit=%d
REACHED` → the retry limit trips an escalating **blocking timer**. `ITD_TheftProtection_Unlock`
is the unlock path; `OpenTheftLine` / safe-line-cut (`ps_PIC_SFL`) and theft-detection
(`ps_PIC_THP`) are the protection lines.

**Diagnostic overrides (the key finding):** the state is overridable over the diag
interface — `THP: Diag: Override CounterPINRetry %d`, `Override Counter Diag`,
`Override Counter UnlockKey`, `Override CurrentState`, `Override Timer Blocking`,
`Override Timer ComfortCoding`, `Override Timer TempUnlock`, `Override ps_PIC_SFL`,
`Override ps_PIC_THP`. **Resetting `CounterPINRetry` via diag is how a brute-forcer
avoids the escalating lockout** — reset the retry counter between attempts. This
explains how community PIN tools work within the 0–1999 space without being blocked.

## Raw CAN message IDs — tooling status
The exact CAN message IDs (per signal) are configured in code (writes to the on-chip
CAN message objects), not a flat table — a data scan for a CAN-ID table was too noisy
(IDs are inline immediates). Extracting them needs **CFG-aware** C166 disassembly.
- Tool: **`hn/c166-dis`** (Perl, GPL) — cloned and **confirmed working** on this image
  (valid C166 decode: `MOV/ADD/JMPR/RETS/BSET`...). Usage:
  `perl c166-dis.pl <file> <start_hex> <len_hex>` (linear sweep, file-relative IP).
  It is ALPHA/linear (no xrefs), so isolating the CAN-object writes from 884 KB of
  mixed code/data is a targeted follow-up, not a one-shot.
- Pragmatic alternative for the CAN emulator: **sniff the live car** (a USB-CAN on the
  infotainment CAN gives the real IDs directly, far faster than full gateway RE).

## Takeaways
1. The theft PIN is gated by a retry-counter + escalating timer, but the counter is
   **diag-overridable** — the actionable mechanism behind PIN recovery.
2. The comfort-CAN signal set + DTC codes are now documented; raw IDs await targeted
   C166 disassembly or a car sniff.
3. A working C166 disassembler is now in hand for any future gateway deep-dive.
