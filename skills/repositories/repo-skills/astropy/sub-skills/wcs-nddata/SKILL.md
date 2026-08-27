---
name: wcs-nddata
description: "Operate Astropy FITS WCS and NDData/CCDData workflows, including
  pixel-world conversion, WCS validation, masks, uncertainties, units, and
  metadata."
metadata:
  disco-role: operating
disable-model-invocation: true
license: BSD 3-Clause
---

# WCS and NDData Router

Use this sub-skill when an Astropy task centers on the relationship between
image-like array pixels and physical/world coordinates, or on carrying image
data together with masks, uncertainties, units, metadata, and WCS.

## Load This When

- A user has FITS WCS header keywords and needs an `astropy.wcs.WCS` object.
- The task asks for pixel-to-world or world-to-pixel conversion.
- The user needs to choose between high-level APE14 WCS calls and legacy
  origin-aware WCS calls.
- The task mentions `all_pix2world`, `all_world2pix`, `pixel_to_world`,
  `world_to_pixel`, `world_to_array_index`, or `array_index_to_world`.
- A FITS header emits WCS warnings or must be validated with `wcslint`.
- The user needs to create or update WCS header cards programmatically.
- The task uses `NDData`, `NDDataArray`, `NDDataRef`, or `CCDData`.
- Image data must keep a boolean mask, `StdDevUncertainty`,
  `VarianceUncertainty`, `InverseVariance`, a unit, metadata, or a WCS object.
- `CCDData.read`, `CCDData.write`, `to_hdu`, FITS `BUNIT`, mask/uncertainty HDUs,
  or WCS-preserving slicing/cutouts are part of the task.

## Route Away When

- FITS file opening, HDU inspection, table formats, ECSV, VOTable, or general
  unified I/O are the main topic; use `../tables-io/SKILL.md`.
- Plotting with WCSAxes, image normalization, RGB rendering, `fits2bitmap`, or
  convolution is the main topic; use `../visualization-convolution/SKILL.md`.
- Coordinate-frame science transforms, `SkyCoord` catalog matching, IERS, or
  `EarthLocation` dominate after the WCS conversion step; use
  `../time-coordinates/SKILL.md`.
- Unit arithmetic, equivalencies, or constants are the main obstacle; use
  `../units-constants/SKILL.md`.
- Install/import, remote data, config/cache, logging, or the general CLI catalog
  is the main topic; use `../cli-config-data/SKILL.md`.

## First Actions

1. Identify the input object: FITS header, FITS file/HDU, existing `WCS`, array,
   `NDData`, `CCDData`, or a world-coordinate object.
2. Record the pixel convention before transforming coordinates.
3. Prefer the high-level WCS API for user-facing coordinates and Astropy objects.
4. Use low-level or legacy WCS methods when the caller needs raw numeric arrays,
   explicit `origin`, or distortion-pipeline control.
5. Inspect `pixel_n_dim`, `world_n_dim`, `array_shape`, `pixel_shape`,
   `world_axis_physical_types`, and `world_axis_units` before assuming axis order.
6. For NumPy indexing, prefer `world_to_array_index` or
   `world_to_array_index_values`, not rounded `world_to_pixel` outputs.
7. For WCS construction from headers, decide whether `relax`, `fix`,
   `translate_units`, `naxis`, and `preserve_units` matter.
8. For image containers, check data shape, unit, mask convention, uncertainty
   type, metadata type, and whether WCS should be attached at construction.
9. Validate with a small round-trip or temporary-file smoke before giving final
   operational code.

## API Selection Rules

- `WCS(header)` is the normal FITS-WCS constructor. It accepts headers,
  dict-like header cards, or a filename, and can also create an empty WCS with
  `naxis=`.
- High-level `pixel_to_world` and `world_to_pixel` return and consume Astropy
  world objects such as `SkyCoord` or `Quantity` when the WCS describes those
  axes.
- High-level methods use Python zero-based pixel coordinates. They do not take
  an `origin` argument.
- Low-level `all_pix2world` and `all_world2pix` include detector, SIP, lookup
  table, and core WCS corrections when present; pass `origin=0` for NumPy-style
  pixels or `origin=1` for FITS/DS9-style coordinates.
- Core `wcs_pix2world` and `wcs_world2pix` omit SIP and table-lookup distortion;
  use them only when that distinction is intentional.
- `array_index_to_world` and `world_to_array_index` use NumPy array order
  `(row, column, ...)`; `pixel_to_world` and `world_to_pixel` use pixel order
  `(x, y, ...)`.
- By default FITS-WCS may normalize angles to degrees and spectral/other units
  to SI. Use `preserve_units=True` when the original header units are the
  required output/input units.
- Use `.celestial`, `.sub(...)`, slicing, or `SlicedLowLevelWCS` when a cube or
  higher-dimensional WCS must be reduced or cut out.

## NDData Selection Rules

- Use `NDData` as a lightweight container for `data`, `uncertainty`, `mask`,
  `wcs`, `meta`, `unit`, and optional PSF information.
- Use `NDDataRef` or `NDDataArray` when slicing, arithmetic helpers, or
  ndarray-like behavior are needed.
- Use `CCDData` for 2D image data that should read/write FITS naturally; a unit
  is required, and a FITS `BUNIT` card is used when reading/writing units.
- Boolean masks follow NumPy masked-array convention: `True` means invalid or
  ignored.
- Use explicit uncertainty classes when propagation matters:
  `StdDevUncertainty`, `VarianceUncertainty`, or `InverseVariance`.
- Attach WCS when constructing `NDData`/`CCDData` when possible. For `CCDData`
  loaded from FITS, WCS keywords are converted to a `WCS` object automatically.
- For cutouts, use `Cutout2D` with a WCS when the cutout must update CRPIX and
  keep pixel/world consistency; confirm distortion limitations first.

## Reference Files

- Use [references/api-reference.md](references/api-reference.md) for verified
  constructor signatures, WCS methods, NDData classes, and CLI/API notes.
- Use [references/workflows.md](references/workflows.md) for self-contained
  recipes: WCS construction, round-trips, WCS header writing, `wcslint`,
  `NDData`/`CCDData`, FITS round-trips, and cutouts.
- Use [references/troubleshooting.md](references/troubleshooting.md) for warning
  handling, axis/order bugs, non-standard headers, WCS convergence failures,
  mask/uncertainty pitfalls, FITS I/O issues, and optional dependency notes.

## Required Safety And Validation

- Do not rely on the original source checkout, tests, examples, or documentation
  at runtime; use only the public installed Astropy package and bundled skill
  references.
- Keep validation temporary-file based when a FITS file is needed, and do not
  overwrite user data unless the user explicitly requested it.
- Treat `wcslint` as diagnostic. Its output can identify suspicious WCS cards,
  but a successful lint does not replace a numeric round-trip check for the
  user’s specific coordinate convention.
- When suppressing `FITSFixedWarning` or FITS verification warnings, state which
  warning was inspected and why ignoring it is safe for the task.
- Verify WCS transformations with at least one pixel/world/pixel or
  world/pixel/world round-trip inside the relevant image domain.
- For `CCDData` workflows, verify that data shape, mask shape, uncertainty
  shape, unit, and WCS metadata survived the read/write/slice/cutout step.

## Native-Backed Validation Ideas

- Tiny in-memory FITS-like header: build a 2D celestial `WCS`, convert a pixel
  to world and back, and check agreement within a small tolerance.
- Distortion-aware check: if SIP or lookup-table distortion is present, compare
  `all_pix2world` against `wcs_pix2world` only to explain the difference, not to
  demand equality.
- `wcslint` smoke: write a temporary FITS file with simple WCS cards and confirm
  that the CLI runs and reports WCS diagnostics without mutating the file.
- `NDData`/`CCDData` smoke: construct data with a mask, unit, metadata,
  `StdDevUncertainty`, and WCS; then slice or FITS round-trip and assert the
  critical attributes remain present.

## Known Boundaries

- This sub-skill does not teach FITS HDU management beyond the amount needed to
  obtain a header or read/write a `CCDData` image.
- This sub-skill does not own Matplotlib WCSAxes plotting or image display.
- This sub-skill does not own astronomy coordinate-frame decisions except as
  WCS inputs or outputs.
- This sub-skill does not require GPU, accelerator, or network resources.
