# EDB POI database (POI.DB3) — schema & custom-POI reference

Source: `EDB/POI/POI.DB3` from CD_8557 (West Europe V17), 1,033,641,984 B, SQLite.
Dumped schema + catalog read-only. This is the reference for the **one supported
map mod**: custom POI.

## Contents (row counts)
- `Poi_BaseAttributes`: **4,525,153** POIs
- `Poi_AddressAttributes`: 4,338,463 (full address)
- `Poi_AlertAttributes`: **0** (no speed-camera data in the VW set — see below)
- `Category_BaseAttributes`: 79 · `PoiPartition_BaseAttributes`: 61
- `String_BaseAttributes`: 5,500,648 · `Language_BaseAttributes`: 14
- Languages: de en fr it es nl cs pt ru no sv pl tr ar

## Core schema
```sql
Poi_BaseAttributes(Poi_ID pk, PoiPartition_ID, Coordinate int, Name_String_ID, Name, PhoneNumber)
Poi_AddressAttributes(Poi_ID pk, HouseNumber/Street/Village/City/Region/Country/IsoCountry/PhoneNumber _String_ID)
Poi_AlertAttributes(Poi_ID pk, SpeedLimit, Direction, TimeStamp, CameraType, FixtureStatus, SeverityRating)
Poi_Relation(Poi_ID, RelationType, Related_Poi_ID)         -- POI↔POI links
Poi_VSegAttributes(Poi_ID pk, VSeg_ID, Direction)          -- POI pinned to a road vseg
Category_BaseAttributes(Category_ID pk, Name_String_ID, Icon_ID, sortorder, brand)
Category_ParentCategory_Relation / PoiPartition_Category_Relation   -- category tree
PoiPartition_BaseAttributes(PoiPartition_ID pk, Icon_ID, LpgAvailable, MapZoomLevel, MapPriority, AlertDistance)
String_BaseAttributes(String_ID pk, Value)
String_TranslationString_Relation(String_ID, Language_ID, Translation_String_ID)   -- i18n
Language_BaseAttributes(Language_ID pk, IsoLanguageCode, Language_String_ID)
Image_* / ImageBlob_BaseAttributes(... ImageData blob) / ImageSet_*   -- icon bitmaps
DatabaseAttribute(Category, Name, Value, Comment)          -- db metadata
PredefinedStatement(Statement_ID pk, Name, Class, Version, Par1, Par2, Par3 blob)
```

## The PredefinedStatement catalog (the query API — a hard constraint)
The firmware's EDB client **cannot run arbitrary SQL** — it calls a fixed catalog of
named statements. Each row is `Class` = `sql` (readable SQL in `Par2`) or `script`
(compiled query bytecode in the `Par3` blob). The catalog (names):
`_init_`, `CurrentDateTime`, `GetNumberOfCategories`, `GetFullPoiData`,
`GetPartitionsOfCategoriesByName1..4`, `GetPoisInRectangle`/`_simple`,
`GetPoisAroundPoint`/`2`, `GetRootCategories`, `GetChildrenOfCategories`,
`GetParentsOfCategories`, `GetDescendantsOfCategories`, `GetPartitionsOfCategories`,
`GetCategoriesByTechnicalName`, `GetCategoryAttributes`, `GetIconAttributes`,
`ImageSet_GetImageDetails`/`List`/`ByName`, `GetPoiPartitionAttributes`,
`CheckForExistentPoisInPoiPartitions`, `GetLanguageAttributes`, `GetStringAttributes`,
`GetPoiAttributes`, `GetRelatedPois`/`Bin`, `GetReverseRelatedPois`, `CopyInputParameter`,
`GetDatabaseAttributes`.

**Consequence for custom POI:** you cannot ship a fresh empty SQLite with only your
POIs — the unit queries through these named statements, so a working custom
`POI.DB3` must **retain the full `PredefinedStatement` catalog** (the compiled
`script` blobs) from a genuine disc, and add your rows into the existing tables.

## Coordinate encoding
`Poi_BaseAttributes.Coordinate` is a **64-bit spatial key**, not a plain lat/lon pair:
nearby POIs share the high bits and differ in the low bits (e.g. `0x971aab67…`,
`0x971aab6c…`, `0x971aab71…` stepping by 5 in the same area) — a Morton/Z-order-style
interleaving of lat/lon, which is what makes `GetPoisInRectangle`/`GetPoisAroundPoint`
efficient. A simple hi=lat / lo=lon split does **not** decode it. The exact
interleave (needed to place a custom POI at a given lat/lon) is a follow-up — derive
it from a few POIs with known coordinates, or reuse an existing nearby POI's key.

## Custom-POI recipe (from the schema)
1. Start from a **genuine POI.DB3** (keep `PredefinedStatement`, categories, partitions,
   languages, icons).
2. Add strings to `String_BaseAttributes` (+ translations if multilingual).
3. Insert `Poi_BaseAttributes` (Poi_ID, a valid PoiPartition_ID, the packed Coordinate,
   Name/Name_String_ID), and optionally `Poi_AddressAttributes`.
4. Assign your POIs to a category/partition (controls icon + map display).
5. **Speed cameras are structurally supported** — `Poi_AlertAttributes`
   (SpeedLimit/CameraType/Direction/SeverityRating) exists but is empty in the VW
   disc, so a custom alert layer is possible in principle (legality/usefulness aside).
