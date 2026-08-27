---
name: environment-cloud
description: "Guides Fiona installation, GDAL and PROJ runtime diagnosis,
  environment scoping, driver discovery, virtual-file paths, and optional
  cloud-session integration."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Fiona environment and cloud access

Use this route when installation fails, compiled extensions cannot load, a
GDAL/PROJ data path is missing, a driver or mode is unavailable, or a workflow
uses local VSI, S3, HTTP, or another virtual-file path. Read [installation and
build](references/installation-and-build.md), [environment API](references/environment-api.md), and [virtual files and cloud](references/virtual-files-and-cloud.md).

Run the safe runtime diagnostic when available:

```console
python scripts/check_runtime.py
```

It reports generic version, driver, and optional-dependency facts without
network, credentials, or data mutation. Read [troubleshooting](references/troubleshooting.md) before changing a GDAL installation.

- Core Fiona vector workflows route to [vector-io](../vector-io/SKILL.md).
- CRS/PROJ transformations route to [crs-transform](../crs-transform/SKILL.md).
- Shell commands route to [cli](../cli/SKILL.md).
- S3 credentials and remote downloads are optional surfaces: stop when the
  task requires credentials, private data, or unapproved network access.
