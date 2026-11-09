# Java UI structure — menus, transitions, engineering screens

Deeper extraction from the Java region of 5238's `FHDD6.FLI`. The UI is romized Jeode
Java (not moddable with public tools — adding new screens is walled), but the
**structure is fully readable**: which screens exist, how they're organised, and which
engineering screens are reachable by coding.

## Organisation (three layers)
- **`Menu_*`** — the individual screens (e.g. `Menu_SERVICE_CALIBRATION`).
- **`MenuNet_*`** — navigation contexts / nets grouping screens (e.g. `MenuNet_SERVICE`).
  An `R`-suffixed twin (`MenuNet_SERVICER`) is the related/return context.
- **`MenuNet_*Rules`** — the **transition graph** for each net (e.g.
  `MenuNet_NAV_MAINRules`, `MenuNet_MEDIARules`). These are the romized rule classes
  that define which screen leads where. Context entry is gated by the
  `allow_context_{media,setup,testmode,tone}` guards (see `FINDINGS.md`).

The 5238 Java region exposes **~822 distinct `Menu_*`/`MenuNet_*` names** (the earlier
"86 screens" was a curated subset of the top-level menu classes).

## Engineering / service / test screens (the hidden tier)
These exist in the shipping image and are gated by coding, chiefly **Testmode
(`0x21=01`)** — which the "modified" discs set, making them reachable without any
firmware patch:

- **Test mode:** `MenuNet_TESTMODE`, `MenuNet_TESTMODE_SYSTEM`.
- **Tuner test/monitor:** `Menu_SVC_TESTMODE_AM_MONITOR`, `..._FM_MONITOR`,
  `..._DAB_MONITOR`, `..._RADIO_MAIN` — live RF/signal monitors per band.
- **Service:** `MenuNet_SERVICE`, `Menu_SERVICE_CALIBRATION`,
  `Menu_SERVICE_DISPLAY_TEST`, `Menu_SERVICE_DIAGNOSIS_CONNECTED`.
- **System / factory:** `MenuNet_SYSTEM`, `Menu_SETUP_SYSTEM_FACTORY`,
  `Menu_SETUP_MAIN_SYSTEM`.
- **Coding / safe code:** `MenuNet_CODE_CHECK`, `Menu_SYS_CODE_INPUT` (the theft/safe
  code entry), `Menu_SVC_TESTMODE_VERSIONINFO` (SW/HW/map versions).
- **Phone lock:** `Menu_PHONE_LOCK_CODE` family.

## Actionable takeaway
The service/test/monitor/version screens are **already in the firmware** — no new UI is
needed and none can be added (the romized wall), but setting **Testmode coding
`0x21=01`** (plaintext, over serial or an SWL disc — see `coding-reference.md`) makes
the hidden engineering tier reachable on the real unit. That's the realistic "hidden
menu" path: unlock existing engineering screens by coding, not by building new ones.

## Note on newer builds
5274/6276 add the `MenuNet_OVERLAY_*` family and SD-import menus on top of this
structure (see `fhdd6-version-diff.md`); the three-layer `Menu_/MenuNet_/…Rules`
organisation is unchanged.
