# FHDD6.FLI cross-version diff (3810 / 5238 / 5274 / 6276)

String-level comparison of the four application images we have.

## Image sizes (not monotonic by index)
| Firmware | FHDD6.FLI size | class |
|---|---|---|
| 3810 | 82,845,636 | C3–C10 |
| 5238 | 85,658,916 | C3–C12 |
| 6276 | 85,828,184 | C14 |
| 5274 | 86,383,388 | C6–C12 (largest) |

## What the newer builds add (6276 and 5274 vs 5238)
6276 has **~45,000 new strings** and **327 new menu screens** over 5238; 5274 has
**603 new menus**. Both 5274 and 6276 (the post-5238 generation) introduce the same
family of newer features:

- **An "overlay" UI layer** — a whole new menu family `MenuNet_OVERLAY_*`
  (OVERLAY_MEDIA, OVERLAY_NAVI, OVERLAY_GENERAL, OVERLAY_NAV_SD_DEST…) that doesn't
  exist in 5238. A layered/overlay HMI paradigm.
- **SD map import** — `MenuNet_NAV_MEM_MANAGE_SD_IMPORT`, `MenuNet_NAV_SD_DEST`,
  `SD_IMPORT_CHOOSE/FAILED/SEL`, `TOUR_SD_IMPORT`. Importing destinations/maps from SD.
- **A richer DAB stack** — `DABTextPlus`, `DABBasicControl`, `DABServiceLinkIn`,
  `DABSmoothDeMute`, `dab_handle_port_read`, DAB linking providers.
- **Expanded media menus** — `MenuNet_MEDIA_AUDIO_*`, `MEDIA_VIDEO_AV/DVD`.

## New coding/settings mechanism — JReg (`MM_SETTINGS`)
The biggest internal change: a **registry-path-based coding/settings system** appears
in the newer builds, alongside the classic `0x400` coding array:

```
<codingentry JRegRootName="TLAUser" JRegPath="/MM_SETTINGS/AudioSettingsService/ENTDYN"
             JRegKey="dynamicCompressionCurve" JRegWriteProperty="true">
<codingentry JRegRootName="TLAUser" JRegPath="/app/TMCSetting"        JRegKey="FM-TMC">
<codingentry JRegRootName="TLAUser" JRegPath="/mixsettings/volume/NAV" JRegKey="last">
<codingentry JRegRootName="system"  JRegPath="/system/uiset/map/color" JRegKey="currentNight">
```

plus a new `data/CCC_Gateway_Coding.xml`. So newer firmware codes many features
through a JReg registry (root `TLAUser`/`system`, paths like
`/MM_SETTINGS/AudioSettingsService`, `/system/uiset/map/color`) rather than only the
flat coding bytes.

## What did NOT change
The **`CL_CODING_*` gateway coding set is identical** between 5238 and 6276 (0 new
`CL_CODING` strings) — the comfort-CAN/diagnostic coding items are stable across
generations. The evolution is in the UI (overlay, SD import) and the JReg settings
layer, not the low-level gateway coding.

## Caveat
5274 and 6276 are **beyond the 680C safe max (~5269)** — these newer features are
informative RE on hardware we would not flash them to, not features obtainable on a
C8/C9 unit. (See `6276-analysis.md` / the compatibility table.)
