# Parquet Raster proposal notes

## Evidence status

These notes capture the supplied Parquet Raster format proposal as an alpha
operating reference. The proposal explicitly says it is work in progress and
not close to the robustness of the main GeoParquet specification. Use this
reference to explain a candidate layout or review metadata; do not use it as a
stable interoperability guarantee.

## File and column layout

A raster column:

- is a Parquet `struct` at the root level of the file;
- contains `crs` (optional UTF-8), `scale_x`, `scale_y`, `ip_x`, `ip_y`,
  `skew_x`, `skew_y` (required doubles), `width` and `height` (required
  `INT32`), and `bands` (required list of byte arrays); and
- has a corresponding top-level `Geometry` or `Geography` column.

The name of that paired spatial column is required in the raster column's
column metadata under `geometry`. Do not assume that the raster struct itself
is the spatial column or that a nested geometry field is an acceptable pair.

At file metadata level, the proposal requires a `version`, `primary_column`,
and `columns` object. `columns` is keyed by raster-column name and contains
column metadata; the required field documented for each raster column is
`geometry`. Implementations may add implementation-specific file metadata,
which readers should ignore when it is not needed.

## Affine georeferencing and indexing

The proposal supports affine georeferencing only. With `ip_x` and `ip_y` as
the world coordinate of the upper-left grid-cell center:

```text
world_x = ip_x + (col + 0.5) * scale_x + (row + 0.5) * skew_x
world_y = ip_y + (col + 0.5) * skew_y + (row + 0.5) * scale_y
```

`col` is zero-based from the left and `row` is zero-based from the top.
`scale_x` and `scale_y` are directional scale factors; `skew_x` and `skew_y`
allow rotated or sheared grids. The proposal says the grid is anchored at cell
centers and calls `ip_x`/`ip_y` the upper-left cell-center coordinate, while
its field table describes them as the upper-left corner. This is an unresolved
alpha wording conflict: apply the published equation when calculating, but
record the terminology conflict rather than silently resolving it. Polynomial
and other non-affine transformations are outside this proposal.

The field descriptions and `pix[w*h]` explanation use `width` for the number
of columns and `height` for the number of rows. One prose sentence reverses
those words (it says width rows and height columns). This is another unresolved
alpha wording conflict. Reviews should use the field descriptions and index
ranges while recording both conflicts, not conceal them.

## Band flags, pixel types, and data

The band encoding contains these logical parts:

| Part | Size/meaning |
| --- | --- |
| `isOffline` | 1 bit; true means values are external and addressed through `RASTERDATA`/URI semantics. |
| `hasNodataValue` | 1 bit; true means the stored `nodata` value is authoritative. |
| `isAllNodata` | 1 bit; a dirty flag indicating all values are expected to be nodata. |
| `isGZIPPed` | 1 bit; true means band data was GZIP-compressed before Parquet compression. |
| `pixtype` | 4 bits; identifies the pixel representation. |
| `nodata` | 1–8 bytes according to pixel type. |
| `length` | `int64`; byte length of `data`. |
| `data` | byte array containing in-db pixel bytes or the encoded out-db reference payload. |

The source also gives the out-db payload its own `length` field as an `int16`
URL-string byte length. Treat this as an alpha schema ambiguity: do not assume
that the generic `int64` length and the out-db `int16` length are the same
physical field unless the candidate encoding makes that explicit.

The proposal's pixel type codes are:

| Code | Pixel type |
| ---: | --- |
| 0 | 1-bit boolean |
| 1 | 2-bit unsigned integer |
| 2 | 4-bit unsigned integer |
| 3 | 8-bit signed integer |
| 4 | 8-bit unsigned integer |
| 5 | 16-bit signed integer |
| 6 | 16-bit unsigned integer |
| 7 | 32-bit signed integer |
| 8 | 32-bit unsigned integer |
| 10 | 32-bit float |
| 11 | 64-bit float |

Code 9 is not assigned in the proposal. Although codes 0, 1, and 2 describe
sub-byte pixel widths, the note says they are still encoded as one byte per
value. Preserve the exact code and byte interpretation in a review; do not
silently coerce a type or fill the code 9 gap.

For in-db data (`isOffline = false`), pixel values are stored row after row.
`pix[0]` is upper-left and `pix[w-1]` is upper-right. The proposal states that
raster data uses little-endian byte order, while its in-db table also mentions
endianness being specified at the start of WKB. Treat the unqualified
little-endian statement as the proposal baseline and record any contrary
container evidence as an alpha ambiguity requiring implementation-specific
confirmation. Do not invent a WKB wrapper or decoder.

For out-db data (`isOffline = true`), the reference payload identifies a
zero-based `bandNumber`, an `int16` URL-string `length`, and a URI string. The
allowed schemes are `file://`, `http://`, and `https://`; examples include
external GeoTIFF files. URI review is metadata-only: validate the scheme and
record the URI as an external dependency without fetching it.

## CRS customization

`crs` is an optional string. Writers and readers are responsible for
serialization and deserialization. For interoperability, the proposal
conventions are:

- `srid:<value>` for a spatial reference identifier; or
- `projjson:<value>` for a PROJJSON document.

These conventions do not authorize guessing or reprojection. A review should
preserve the exact CRS text, identify its convention when recognizable, and
mark absent, malformed, or unsupported text as unresolved.

## Proposal limitations

The proposal does not establish the maturity or behavior of a complete raster
implementation. In particular, this bundle does not provide:

- a validator, executable fixture, or conformance test suite;
- a mandated compression, chunking, or external-file access policy beyond the
  listed URI schemes;
- a complete definition for packing the flag and pixel-type bits into bytes;
- a resolution of the width/height wording conflict or the endianness wording
  tension;
- a guarantee that readers support every listed pixel type, CRS encoding, or
  URI scheme; or
- stable GeoParquet vector validation.

For vector-only interpretation or validation, follow the sibling
[validate-geoparquet](../../validate-geoparquet/SKILL.md) skill. Keep its result
separate from any alpha raster proposal assessment.