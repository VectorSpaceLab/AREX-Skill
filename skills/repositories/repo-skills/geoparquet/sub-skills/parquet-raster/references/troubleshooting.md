# Parquet Raster troubleshooting

This is a bounded review guide for an alpha proposal. It does not supply a
validator or a raster decoder.

## Missing or unknown file metadata

**Symptom:** The file lacks one of the proposal's required `version`,
`primary_column`, or `columns` metadata fields, or its proposal version cannot
be identified.

**Action:**

1. Preserve the raw file metadata and report exactly which required key is
   absent or unreadable.
2. Check that `primary_column` names a raster column represented in `columns`;
   do not infer a primary raster from Parquet column order.
3. Treat an unknown version or schema revision as unresolved proposal
   metadata. Do not claim stable interoperability or silently apply a newer or
   older schema.

## Malformed raster struct

**Symptom:** A candidate raster column is nested rather than root-level, is not
Parquet `struct`, or lacks a required field or expected type.

**Action:**

1. Enumerate the root-level column and compare its fields with `crs` (optional
   UTF-8), the six required `DOUBLE` affine fields, `width` and `height`
   (`INT32`), and `bands` (`List<BYTE_ARRAY>`).
2. Report the exact missing, nested, or mistyped field as an incomplete alpha
   proposal layout.
3. Do not decode bands or substitute a nearby struct until the schema issue is
   explicitly resolved.

## Band flag or length mismatch

**Symptom:** `isOffline` conflicts with the available payload, a declared length
cannot be reconciled with the exposed bytes, or the flag/pixel-type encoding
cannot be decoded safely.

**Action:**

1. Preserve the raw flags and `pixtype`; the proposal does not completely
   define how their bit fields are packed, so do not invent a byte layout.
2. For in-db data, compare the generic `length` with the byte count of `data`
   only when both are explicitly exposed in that representation.
3. For out-db data, check the zero-based `bandNumber` and compare the `int16`
   URL-string length with the encoded URI only when the out-db payload exposes
   that field separately. The source also describes a generic `int64` data
   length, so report which interpretation was used rather than conflating the
   two.
4. If `isOffline` is true, treat pixel access as external; if it is false, do
   not interpret a URI as in-db pixel bytes. Report the band as unresolved when
   the flags and payload disagree.

## Missing paired geometry or geography column

**Symptom:** The raster column's metadata names `tile_geom`, but no top-level
column with that name exists, or the named column is not a `Geometry` or
`Geography` column.

**Action:**

1. Confirm the candidate raster column is a root-level Parquet `struct`.
2. Read the exact `geometry` metadata value; do not infer a name from the
   raster column or from `primary_column`.
3. Enumerate only top-level columns and compare exact names and types.
4. Report the pair as unresolved if the named column is absent, nested, or has
   the wrong spatial type. Do not silently select a different geometry column.
5. Route any resulting vector metadata or validity question to
   [validate-geoparquet](../../validate-geoparquet/SKILL.md).

This is a schema/metadata failure or an incomplete proposal implementation,
not evidence that the raster data can safely be read without the pair.

## Safely reviewing an `https://` out-db band

**Symptom:** A band has `isOffline = true` and an `https://` URI.

**Action:**

1. Check that the URI is syntactically represented as an allowed `https://`
   scheme and that the metadata's `bandNumber` is present as a zero-based
   external band reference.
2. Compare the declared URL-string `length` with the encoded metadata only if
   the representation exposes enough information to do so safely.
3. Record that pixel values are external and that the URI is an unverified
   dependency.
4. Do **not** issue HTTP requests, follow redirects, resolve credentials,
   download the file, inspect a remote GeoTIFF, or claim pixel-level validity.
5. If actual pixel access is required, stop and request an explicitly approved,
   separately provisioned retrieval workflow; this skill cannot perform it.

An allowed scheme is not proof that the endpoint is reachable, trusted, or
contains the expected raster band.

## Other review symptoms

### `nodata` appears but `hasNodataValue` is false
Ignore the stored nodata bytes for semantic masking and report that the value
is not authoritative under the proposal.

### `isAllNodata` is true
Report it as a dirty implementation flag. Do not treat it as independently
verified content, especially for out-db data.

### Unknown `pixtype` or code 9
Preserve the raw code and mark decoding unresolved. Do not choose a nearby
pixel type. Remember that the proposal leaves code 9 unassigned and uses one
byte per value for codes 0–2 despite their sub-byte labels.

### Affine result looks unexpected
Recalculate with zero-based `col`/`row`, add `0.5` to both indices, and use
all four scale/skew terms. Check whether the source has a rotated or sheared
grid; do not replace skew with zero. Record the proposal's width/height prose
conflict if dimensions are being interpreted.

### CRS is absent or not prefixed
Preserve the exact value and mark CRS interpretation unresolved. Do not assume
a default CRS or reproject values. Recognizable `srid:` and `projjson:` forms
are conventions, not permission to validate an external authority or alter the
raster.

### A request asks whether a vector file is GeoParquet-valid
Do not answer from this alpha raster skill. Follow
[validate-geoparquet](../../validate-geoparquet/SKILL.md) and keep raster
proposal caveats separate.