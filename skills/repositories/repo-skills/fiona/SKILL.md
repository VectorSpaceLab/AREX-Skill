---
name: fiona
description: "Guides Fiona workflows for GDAL-backed vector data I/O,
  GeoJSON-like features and schemas, CRS transforms, local virtual files,
  cloud-session boundaries, and the fio CLI."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Fiona repository skill

Fiona is a Python interface for reading and writing vector data through GDAL/OGR.
Use this graph when a task mentions Fiona, `fiona.open`, `Collection`,
`MemoryFile`, `Feature`, `Geometry`, `CRS`, `fio`, GeoPackage, Shapefile, GeoJSON
conversion, VSI paths, or Fiona/GDAL installation problems.

## Start here

1. Confirm the installed Fiona/GDAL/PROJ combination and supported drivers. For
   installation and runtime failures, read [troubleshooting](references/troubleshooting.md)
   and the [provenance snapshot](references/repo-provenance.md).
2. Choose one focused route:
   - [vector-io](sub-skills/vector-io/SKILL.md): Python read/write/append,
     collections, schemas, models, layers, encodings, MemoryFile, and local VSI.
   - [cli](sub-skills/cli/SKILL.md): `fio` inspection, streaming, conversion,
     metadata, bounds, and safe pipelines.
   - [crs-transform](sub-skills/crs-transform/SKILL.md): CRS definitions,
     coordinate/geometry transforms, and PyProj/Shapely boundaries.
   - [environment-cloud](sub-skills/environment-cloud/SKILL.md): compiled
     installation, GDAL/PROJ data, drivers, Env, openers, and optional cloud
     sessions.
3. For a task crossing routes, keep one explicit source/destination CRS and one
   schema owner; link the relevant sibling route rather than duplicating details.

## Installation and smoke check

For a normal public install:

```console
python -m pip install fiona
python -c "import fiona; print(fiona.__version__, fiona.__gdal_version__)"
```

Use a compatible conda-forge or source build when you need format drivers not
present in a wheel. Do not mix incompatible GDAL binary stacks. The checked
repository line requires GDAL >=3.1 at source-build time; current public
releases may document newer minimums, so inspect the installed package before
pinning a deployment.

For a generic diagnostic that does not expose local paths or credentials, run
[the bundled runtime checker](sub-skills/environment-cloud/scripts/check_runtime.py).

## Operating rules

- Use context managers for collections and memory files; close external
  resources deterministically.
- In write mode, provide a supported driver and schema, and usually a CRS.
  Reopen outputs and validate driver, schema, CRS, bounds, and representative
  features instead of checking only file existence.
- Treat collections as streams: iteration consumes the cursor and dataset IDs
  are GDAL-controlled, not necessarily contiguous Python indexes.
- Fiona transports feature data; it does not replace Shapely for geometry
  operations or PyProj for advanced transformation control.
- Treat HTTP/S3/GS paths, requester-pays access, credentials, and destructive
  `fio rm` as explicit side-effect boundaries. Stop for missing authorization.

## Scope and limitations

This graph covers the public package and CLI surfaces evidenced by the source,
docs, examples, and representative tests. It intentionally excludes vendored
implementation, CI/release automation, destructive verification, unapproved
network/credential use, and long-running or large-data operations. Read
[troubleshooting](references/troubleshooting.md) for those boundaries.
