# Tables and I/O API Reference

## Table APIs

- `Table(data=None, masked=False, names=None, dtype=None, meta=None, copy=True, rows=None, copy_indices=True, units=None, descriptions=None, **kwargs)` creates an in-memory table.
- `QTable(...)` behaves similarly but preserves quantity/mixin columns more naturally.
- Common operations: `table.add_column`, `table.remove_column`, `table.rename_column`, `table.group_by`, `table.sort`, `table.write`, `Table.read`, `join`, `vstack`, `hstack`.
- Use `table.meta` for table-level metadata and column `.unit` / `.description` for column metadata.

## Unified I/O

`Table.read(*args, **kwargs)` and `Table.write(*args, serialize_method=None, write_indices=False, **kwargs)` route through Astropy's I/O registry.

Important options:

- `format=`: name the format explicitly (`ascii.ecsv`, `fits`, `votable`, `ascii.csv`, `ascii.fixed_width`, `hdf5`, `parquet`, etc.).
- `overwrite=True`: only when overwriting is explicitly intended.
- `serialize_method=`: controls mixin serialization for formats that need it.
- `path=` or format-specific kwargs: some formats require HDU/path/table names.

## FITS APIs

- `fits.open(name, mode='readonly', memmap=None, save_backup=False, cache=True, lazy_load_hdus=None, ignore_missing_simple=False, use_fsspec=None, fsspec_kwargs=None, decompress_in_memory=False, **kwargs)` opens a FITS file as an `HDUList`.
- Use `fits.getdata`, `fits.getheader`, `fits.writeto`, `fits.append`, `fits.update`, and `fits.info` for convenience operations.
- HDU classes include `PrimaryHDU`, `ImageHDU`, `BinTableHDU`, `CompImageHDU`, and `HDUList`.
- Verification controls appear as `output_verify=` on writes and `verify()` methods on HDUs/lists.

## CLI/API Mapping

| Command | API family | Default safety |
| --- | --- | --- |
| `fitsinfo` | `fits.info`, HDU summaries | read-only |
| `fitsheader` | FITS header display | read-only |
| `fitsdiff` | FITS comparison | read-only when output path not overwriting |
| `fitscheck` | FITS checksum/verification | can mutate with update/checksum flags |
| `showtable-astropy` | Table display | read-only |
| `volint` | VOTable validation | read-only validation |
