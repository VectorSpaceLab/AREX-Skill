# Safe `fio` pipeline recipes

## Inspect and stream

```console
fio info input.geojson --indent 2
fio cat input.geojson --compact
fio cat input.geojson | fio bounds --with-id
```

The default `cat` output is a sequence of feature JSON objects. Use `--rs` when
piping to tools that expect RFC 7464 record separators; preserve the framing
choice through the whole pipeline.

## Convert a stream to a dataset

```console
fio cat input.geojson | fio load output.gpkg --driver GPKG --layer features
fio info output.gpkg --layer features --count
```

`fio load` infers the output schema from the first feature. Validate that the
remaining features have compatible geometry and property types before using a
large stream. For a known schema or complex conversion, prefer the Python route
in `vector-io`.

## Collection and distribution

```console
fio cat input.geojson | fio collect --indent 2 > collection.json
fio distrib < collection.json | fio collect > roundtrip.json
```

Use `collect --src-crs EPSG:3857` only when the input geometries really are in
that CRS; it transforms them to EPSG:4326 and requires parseable GeoJSON.

## Add a derived property

```console
fio cat input.geojson | fio calc total 'f.properties.a + f.properties.b'
```

If `total` already exists, the command stops unless `--overwrite` is explicit.
Use a disposable output or redirect only after checking the expression and
schema. `calc` is optional and should not be treated as a general safe Python
interpreter.
