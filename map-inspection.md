# Map inspection — CD_8557 (West Europe V17)

Inspection of a West Europe V17 map disc (`CD_8557.iso`, 6.8 GB), mounted read-only;
small schema files extracted for analysis. (The map binaries are copyrighted and not
included here — this documents the **format**, matching and extending krcenov's spec.)

## Identity (cdrom.toc / DBINFO / DatabaseAttribute)
- Volume **CD_8557**, dated 2019-11-05; db **EU (2019Q1)**, Area **West Europe**,
  Supplier **Navteq/HERE**.
- Version 505.20.910.1.84, **Customer Version V17**, Customer VW. TMC 2019-06-10.
- EDB EDB_20190919 (core 1.01, poi 2.07). DBAL V006.047–V010.015 (the same versions
  krcenov documented).

## Format = krcenov's RNS-510 spec, `eu` (WEU) prefix vs their `eeu` (EEU)
- `files.cfg`: 39 file IDs, compression types 0 NOT / 1 FLAT / 2 MAP / 3 FEATURE —
  identical scheme.
- `db/eu.rd` 786 MB road/routing graph, `eu.cty` cities, `eu.il`/`eu.iof` indexes,
  `eu.mod` schema (SIEMENS header, names the **Arriba** nav engine), `eu.tmc`,
  `eu.typ` (multilingual street types: ES/EN/IT/DE/FR/NL/PL/Basque).
- `db/euz.mp0` 2.06 GB render tiles + `euz.mg1–4` generalized, `euz.rt/rl/prl/prd`
  name-search + phonetic, `euz.cl/ct` city search, `euz.fea` gazetteer. All
  MAP_COMPRESSED from the production tree.
- `config/create_cd` leaks build provenance — an internal Navteq production-tree path
  (redacted here).

## POI database (EDB/POI/POI.DB3, 1.03 GB SQLite)
- **4,525,153 POIs** (4,338,463 with full address: house/street/city/region/country/
  ISO), 5,500,648 strings in **14 languages**, 79 categories, 61 POI partitions,
  82 icon blobs.
- Categories: gas/CNG stations, restaurants, tourist attractions, hotels, parking,
  ATM, pharmacy, bank, museums, police, train/transport, border crossing, rest area,
  brand services (VW/Seat/Skoda/Bentley), etc.
- **No speed-camera data** — `Poi_AlertAttributes` (SpeedLimit/CameraType/
  FixtureStatus) has 0 rows.
- 35 `PredefinedStatement`s (the fixed EDB query catalog krcenov described — clients
  cannot run arbitrary SQL).
- An internal ClearCase config-spec leaks a Siemens navicore/Arriba source-tree path
  and a 2011 build timestamp (details redacted).

## Takeaways
- This disc's structure is exactly the published RNS-510 map format (WEU `eu`
  prefix), so krcenov's EEU tooling/notes transfer directly.
- POI data is a standard SQLite `.db3` behind a fixed query catalog — the supported
  extension point (custom `POI/*.db3`), not a route-geometry editor.
- No speed-camera layer ships in this VW set.
