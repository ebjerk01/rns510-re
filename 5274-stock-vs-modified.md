# RNS-510 FW 5274 — stock vs. "modified" diff

A byte/tree comparison of the two 5274 update ISOs:
- stock: `RNS_510_FW_5274_update.iso`
- modified: `RNS_510_FW_5274_update_modified.iso`

Both are the same Continental delivery build **`C_EU_13.274_t2`**; the "modified"
disc is the genuine Continental 5274 re-authored by a community modder (its own
`VERSION.TXT` says so: *"This is an unofficial SWL CD by josi. Use it at your own
risk."*).

## What the modification actually is

Worth knowing before trusting any "modified" disc: it is **not** a coding/feature
injection. It is a **hardware-compatibility widening + variant trim**, with the CRC
recomputed.

### 1. Hardware coverage extended
`VERSION.TXT`:
- `#Steckbrief: C_EU_13.274_t2 C10/C12` → `… C6/C10/C12`
- `#AppsBuild:  C_EU_13.274_t2 C10/C12` → `… C6/C10/C12`
- `#CRC16: af2a` → `6dbc` (recomputed after the edits; advisory anyway — see FINDINGS)

### 2. HW-ID / project gating relaxed
- `*/HWIDMAP.TXT` 145→69 B: removed explicit `000100020041/42/43 SILVER_1` HW-ID rows.
- `*/PRJCTMAP.TXT` shrank: removed the `EURTO` and `EURBM` variant project rows.
- Removed every `EURBM/` + `EURTO/` `CONFIG/DLSCRIPT.TXT` (APPS/HOST/SWL/VUCI).
Net: the branch logic that picks/rejects a market variant is trimmed to one path.

### 3. Coding scripts: formatting only — NOT what people assume
The `WA/*.WSH` scripts grew ~+69 B each, but the diff is **whitespace + a
commented-out per-script `ld < /tffs0/lib/diag/CodingTest.out`** (the coding lib is
loaded once globally instead). Critically, **`# Testmode: Active` and
`# Speed limit DVD/TV: 300km/h` are present in BOTH stock and modified** — the
testmode and 300 km/h video-in-motion lines are in the Continental *delivery*
scripts already; the modder did not add them. The `SetRegDataHex`/`SetCoding`
values are unchanged between the two. One script is added in modified:
`WA/EURSEHDD.WSH`.

## Compatibility is gated by BLSCRIPT, not the Steckbrief
Despite the Steckbrief listing C6/C10/C12, what actually gates loading is
`BLSCRIPT.CFG`. The modified 5274's BLSCRIPT has match blocks for `0x000201XX`,
`0x0002XXXX`, `0x0005XXXX` **and `0x0006XXXX`** (HW_MODULE 01.08 / HW_VERSION 01.01
/ CUSTOMER_PRODUCT 01.07). A unit whose HW Radio ID is `0006` is matched by the
`[0x0006XXXX…]` block, so the bootloader accepts the disc even though the Steckbrief
text does not spell out that hardware class.

## Takeaways
- The "modified firmware" mystique is mostly **compatibility widening + CRC fix**,
  not secret feature unlocks.
- Testmode + 300 km/h video-in-motion are **stock** in the delivery coding scripts.
- The `0x0006XXXX` BLSCRIPT match block is the thing to preserve when building a
  custom flash/SD disc for a 0006-class radio.
