---
name: parquet-raster
description: "Review and reason about the alpha Parquet Raster proposal: root
  raster structs, paired GeoParquet geometry/geography columns, affine
  georeferencing, bands, storage location, CRS, and proposal limits."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Parquet Raster (alpha proposal)

## Status and scope

Treat this skill as an **alpha proposal review aid**, not as stable GeoParquet
vector support. The proposal describes raster values in Parquet and relies on
GeoParquet/Parquet geometry or geography types for a paired spatial reference
column. It is suitable for schema review, metadata interpretation, and safe
out-db URI inspection. It is not a claim that a file is interoperable, nor a
replacement for a production raster reader or validator.

Use this skill when a task mentions a proposed Parquet Raster column or needs to
interpret its raster metadata. For vector metadata, vector validity, or stable
GeoParquet questions, follow [validate-geoparquet](../validate-geoparquet/SKILL.md)
instead.

## Operating procedure

1. **Check proposal metadata and locate the raster column.** Record the
   file-level `version`, `primary_column`, and `columns` metadata before
   interpretation; missing or unknown values are unresolved proposal metadata,
   not evidence of a default version. Confirm that each raster column is a
   root-level Parquet `struct`. Its struct contains the raster value fields
   described in [the bundled proposal notes](references/raster-proposal.md),
   including required affine parameters, dimensions, and `bands`.
2. **Resolve the paired spatial column.** Find a top-level `Geometry` or
   `Geography` column. The raster column's column metadata must name it in the
   required `geometry` field. A missing, nested, mistyped, or mismatched pair
   is an alpha proposal issue; do not silently substitute another vector
   column.
3. **Interpret georeferencing.** Apply the center-of-cell affine equations
   below using zero-based `col` from the left and `row` from the top. Preserve
   the source values and units; do not assume north-up, square pixels, or a
   particular axis order.
4. **Inspect bands.** Decode the band flags and `pixtype` before interpreting
   `nodata`, `length`, or `data`. For in-db bands, expect row-major pixel bytes.
   For out-db bands, review the URI and band number without dereferencing it.
5. **Check CRS representation.** `crs` is optional UTF-8 text. Recognize the
   proposal's `srid:value` and `projjson:value` conventions, but do not invent
   a CRS when it is absent or malformed.
6. **Report proposal limits.** Label conclusions as proposal-level and record
   ambiguities or unsupported behavior. Do not promote this skill's result to
   stable vector compliance.

For a cell at zero-based column `col` and row `row`, the proposal gives:

```text
world_x = ip_x + (col + 0.5) * scale_x + (row + 0.5) * skew_x
world_y = ip_y + (col + 0.5) * skew_y + (row + 0.5) * scale_y
```

The proposal describes `width` as the pixel width and `height` as the pixel
height; therefore use `0 <= col < width` and `0 <= row < height`. Keep two
alpha wording conflicts visible: one prose sentence says grids have `width`
rows and `height` columns, and the field table/equations describe `ip_x` and
`ip_y` like a corner origin while another paragraph calls them the upper-left
cell center. Apply the published equation when calculating, but do not claim
these descriptions are reconciled.

## Required review observations

A useful review should be able to state:

- whether the file-level `version`, `primary_column`, and `columns` metadata is
  present and internally referable, while preserving unknown version/schema
  details as unresolved;
- which root-level struct is the raster column and which top-level geometry or
  geography column it names;
- whether all required affine fields and `INT32` dimensions are present, while
  treating validation of numerical suitability as an explicit review decision;
- the pixel coordinate convention and the resulting world coordinate for any
  requested cell;
- each band's `isOffline`, `hasNodataValue`, `isAllNodata`, `isGZIPPed`,
  `pixtype`, `nodata`, `length`, and `data` interpretation;
- whether bytes are in-db or the band is out-db, and whether an out-db URI uses
  an allowed `file://`, `http://`, or `https://` scheme;
- the CRS text and whether it follows the `srid:` or `projjson:` convention;
- which observations are proposal-supported, ambiguous, unverified, or out of
  scope.

## Safety and non-goals

- Never fetch, open, authenticate to, or resolve an out-db URI during a review.
  An `https://` URI can be checked syntactically and reported as an external
  dependency without network access.
- Do not treat `isAllNodata` as proof of content: the proposal calls it a dirty
  flag and says it is set properly by an implementation operation. If it is
  true, report the flag and its provenance; do not scan external data.
- Do not infer pixel values from `nodata` unless `hasNodataValue` is true.
- Do not assume a missing `crs` means a default CRS.
- Do not create a raster validator, fixture, decoder, or network fetcher for
  this skill. No such validator or fixture is part of this alpha proposal
  bundle.
- Do not use this skill to answer vector questions; route those to
  [validate-geoparquet](../validate-geoparquet/SKILL.md).

## References and troubleshooting

- [Raster proposal notes](references/raster-proposal.md) summarize the source
  contract, field encodings, equations, and known limitations.
- [Troubleshooting](references/troubleshooting.md) gives bounded recovery steps
  for common review failures, including malformed schema/metadata, band
  length/flag ambiguity, a missing paired column, and a remote out-db band.

When reporting a result, include the inspected schema/metadata facts, the
proposal interpretation used, any source ambiguity, and the actions explicitly
not taken (such as fetching a URI).