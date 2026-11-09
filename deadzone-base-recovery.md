# The FHDD6 ">9 MB dead zone" — resolved (no second base needed)

The earlier analysis (`3810-analysis.md`) concluded the native region past ~9 MB used
a different, unrecovered load base, which blocked decompiling `httpAccessCheck` /
`DevAccessCheck` (the USB-RNDIS diagnostic web-server gate). **That was a
misdiagnosis.** The original base `0xf688dcf4` holds well past 9 MB.

## Evidence
The symbol table around the mangled symbol
`httpAccessCheck__C17OslibHttpServer_cG11sockaddr_in` (file offset 3,194,659, in the
valid range) holds address fields in the `0xf71xxxxx` range. Resolving them under
`VA = file_offset + 0xf688dcf4`:

| Symbol VA | → file offset | content |
|---|---|---|
| `0xf7112fb0` | 0x8852bc (8.93 MB) | **valid PPC code** (`addi r28,r11,0x10` / `add r3,r26,r3` / `lha r0,0x10(r11)` / `mtlr`) |
| `0xf7188dd0` | 0x8fb0dc (9.4 MB) | symbol/filename `…/trafficsituationdetails.h` |
| `0xf7393c3c` | 0xb05f48 (11.5 MB) | mangled symbol `…CfcChar…` |

Code, filenames and symbols all resolve cleanly at `0xf688dcf4` at 8.9–11.5 MB — i.e.
the base is continuous through the "dead zone". No second base exists to recover.

## Why the earlier searches failed
The original pass looked for `lis/addi` (absolute) immediate loads of the HTTP log
string addresses and found none — and ad-hoc searches for an absolute BE32 pointer to
those strings also find none. That is because the code references `.rodata` strings
**via the GOT / a pointer table (r2-relative), not absolute `lis/addi`**. So the refs
are real but invisible to an absolute-immediate or raw-pointer scan. A GOT-aware
disassembler (Ghidra) resolves them; hand scans do not. The absence of `lis/addi`
hits was mistaken for "wrong base".

## Consequence — httpAccessCheck is now decompilable
The whole native region (not just 1.2–9 MB) is addressable at `0xf688dcf4`. The
remaining step to answer "does a production unit serve the USB-RNDIS web control
panel, and what does `httpAccessCheck` allow?" is a **full-region Ghidra import at
base `0xf688dcf4`** (the earlier Ghidra project was imported only for the 1.2–9 MB
sub-range, which is what truncated the analysis) with auto-analysis + GOT/pointer
resolution, then decompile `httpAccessCheck` / `DevAccessCheck`. No exotic base
recovery is required — that blocker is removed.

## Correction
`3810-analysis.md`'s note that the >9 MB region "uses a different/again-unrecovered
base" is **superseded** by this — the base is `0xf688dcf4` throughout; the HTTP string
refs are GOT-based, not absolute.
