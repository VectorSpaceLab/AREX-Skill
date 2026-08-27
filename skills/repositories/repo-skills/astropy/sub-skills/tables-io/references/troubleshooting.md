# Tables and I/O Troubleshooting

## Units or Metadata Lost After Round-Trip

Use `QTable` and `format="ascii.ecsv"` when possible. FITS and generic text
formats may not preserve all mixin metadata exactly. After reading, assert the
critical columns, units, and metadata.

## Format Guessing Picks the Wrong Reader

Specify `format=` explicitly. For ASCII variants, use names such as
`ascii.ecsv`, `ascii.csv`, `ascii.fixed_width`, `ascii.ipac`, or `ascii.cds`.
For multi-extension FITS, specify `hdu=` or extension name where the API accepts
it.

## FITS Verification Warnings

Warnings can indicate non-standard but common legacy files. Inspect the header
cards and choose a policy:

- Strict output you generate: `output_verify="exception"`.
- Legacy input you inspect: read with warning capture and document which issue
  is accepted.
- Do not globally silence warnings before understanding the affected HDU.

## Memory or Lazy Loading Surprises

FITS files can use memory mapping and lazy HDU loading. Keep the `HDUList`
context open while accessing data. If data must outlive the file handle, copy it
explicitly.

## Optional Dependency Missing

Install the smallest needed dependency:

- HDF5: `h5py`.
- Parquet: `pyarrow`.
- HTTP/S3 remote access: `fsspec` extras and `s3fs` for S3.
- Pandas bridge: `pandas` and any required dataframe dependency.

## CLI Mutated or Overwrote a File

Use temporary copies and avoid mutating options by default. In particular,
`fitscheck` can update checksum-related state; only use modifying flags when the
user asked for that result and a backup exists.
