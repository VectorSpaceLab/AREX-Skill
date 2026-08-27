# `fio` CLI reference

The console entry point is `fio = fiona.fio.main:main_group`. Start with:

```console
fio --help
fio --version
fio --gdal-version
fio env --formats
```

## Core commands

- `fio info INPUT` emits dataset metadata as JSON. `--count`, `--bounds`,
  `--crs`, `--name`, and `--format/--driver` select one value.
- `fio ls INPUT` emits layer names.
- `fio cat INPUTS...` emits GeoJSON features as a sequence. Use `--bbox
  w,s,e,n`, `--where TEXT`, `--layer`, `--dst-crs`, `--rs`, `--precision`,
  `--indent`, or `--compact` as appropriate.
- `fio dump INPUT` emits a FeatureCollection by default. `--x-json-seq` or
  cat is preferable when a streaming sequence is needed; `--encoding` handles
  non-default input encoding.
- `fio load OUTPUT --driver DRIVER` reads a FeatureCollection or feature
  sequence from stdin and infers a basic schema from the first feature. Use
  `--src-crs`, `--dst-crs`, `--layer`, creation/open options, or `--append`.
- `fio bounds` reads GeoJSON objects from stdin and prints bounding boxes.
  `--with-id`, `--with-obj`, `--explode`, `--precision`, and `--rs` alter the
  output.
- `fio collect` turns a feature sequence into a FeatureCollection; `fio
  distrib` does the inverse.

## Optional expression commands

`fio calc PROPERTY EXPRESSION` evaluates a restricted expression namespace over
features. The namespace includes common reductions/conversions, `math`, an
optional Shapely `shape`, and `f` for the current feature. Existing properties
are not overwritten unless `--overwrite` is passed. `map`, `filter`, and
`reduce` are also optional in this development line and need the calc extra.

Install the documented `calc` extra when these commands are selected. Treat
expressions and input as data validation surfaces; do not pass untrusted code
or assume arbitrary Python is allowed.

## Destructive command

`fio rm INPUT [--layer NAME] [--yes]` removes a datasource or layer. It is
excluded from routine native verification. Use it only after explicit human
confirmation, with a disposable fixture and a clear rollback plan.
