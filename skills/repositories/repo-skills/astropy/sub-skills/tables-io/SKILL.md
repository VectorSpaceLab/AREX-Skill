---
name: tables-io
description: "Use Astropy Table, QTable, unified I/O, FITS, ASCII/ECSV, VOTable,
  optional file-format integrations, and table/FITS command-line tools."
metadata:
  disco-role: operating
disable-model-invocation: true
license: BSD 3-Clause
---

# Tables and I/O Router

Use this sub-skill when a task centers on Astropy tables, file formats, FITS
HDU operations, unified read/write behavior, or table/FITS command-line tools.

## Load This When

- The user asks for `Table`, `QTable`, columns, units in tables, masked data,
  metadata, grouping, indexing, joining, stacking, or sorting.
- The task reads/writes FITS, ASCII, ECSV, VOTable, HDF5, Parquet, YAML, or
  pandas/dataframe-like objects through Astropy.
- The task uses `Table.read`, `Table.write`, `fits.open`, `fits.info`,
  `PrimaryHDU`, `BinTableHDU`, `HDUList`, `Header`, or FITS verification.
- The command names `fitsinfo`, `fitsheader`, `fitscheck`, `fitsdiff`,
  `showtable-astropy`, or `volint` are involved.

## Route Away When

- FITS WCS interpretation or pixel/world conversion is central; use
  `../wcs-nddata/SKILL.md`.
- Image display, normalization, RGB output, or `fits2bitmap` dominates; use
  `../visualization-convolution/SKILL.md`.
- Unit conversion is the main difficulty; use `../units-constants/SKILL.md`.
- General install/config/remote-data behavior is the main issue; use
  `../cli-config-data/SKILL.md`.

## First Actions

1. Identify the object boundary: in-memory table, FITS HDU/file, text table,
   VOTable, or optional backend format.
2. Prefer `QTable` when columns should retain `Quantity` and mixin objects.
3. Use explicit `format=` for non-obvious reads/writes; do not rely on file
   extension guessing when correctness matters.
4. For round-tripping units/metadata, prefer ECSV for tables unless the user
   requires another format.
5. For FITS, decide HDU type, extension name/index, memmap mode, verification
   policy, and whether the operation may mutate a file.
6. Use optional dependencies only when the selected format needs them.
7. Validate with a temporary read/write round-trip or CLI help/tiny-fixture
   check.

## References

- [references/api-reference.md](references/api-reference.md) lists table, FITS,
  registry, and selected I/O APIs.
- [references/workflows.md](references/workflows.md) gives table creation,
  ECSV/FITS round-trips, FITS HDU operations, joins, grouping, and optional
  format patterns.
- [references/formats-and-cli.md](references/formats-and-cli.md) summarizes
  format choices and command-line safety.
- [references/troubleshooting.md](references/troubleshooting.md) covers unit
  loss, FITS verification warnings, memmap/lazy loading, optional dependencies,
  and CLI mutation hazards.

## Safety and Validation

- Never run a file-mutating FITS CLI option on user data without explicit
  approval and a backup/copy.
- Prefer temporary output paths for format experiments.
- Check table column units and metadata after round-trip if the task depends on
  them.
- Use explicit HDU selection when a FITS file contains multiple extensions.

## Native-Backed Validation Ideas

- Write a `QTable` with quantity columns to ECSV and assert units round-trip.
- Create a tiny FITS image, open it with `fits.open`, and assert HDU shape.
- Run `fitsinfo --help`, `fitsheader --help`, and `showtable-astropy --help` as
  parser checks.
