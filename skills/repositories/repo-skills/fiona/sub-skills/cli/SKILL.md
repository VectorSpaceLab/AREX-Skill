---
name: cli
description: "Guides Fiona's fio command-line inspection, conversion, GeoJSON
  streaming, metadata, filtering, and safe pipeline workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Fiona `fio` CLI

Use this route for shell commands that inspect, stream, convert, or summarize
vector datasets. Read [CLI reference](references/cli-reference.md) for command
flags, [pipeline recipes](references/pipeline-recipes.md) for composable
examples, and [troubleshooting](references/troubleshooting.md) before changing
input framing or driver options.

Common routes are `fio info`, `fio ls`, `fio cat`, `fio dump`, `fio load`,
`fio bounds`, `fio collect`, and `fio distrib`. `fio calc` and the expression
commands require the optional calc dependencies. `fio rm` is destructive and is
not a routine verification operation; require deliberate user approval and
never add it to an unattended pipeline.

Use `vector-io` for the equivalent Python API, `crs-transform` for CRS
semantics, and `environment-cloud` for GDAL driver, AWS, or virtual-file setup.
