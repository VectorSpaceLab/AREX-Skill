---
name: spikevision
description: "Legacy neuromorphic dataset wrappers and transforms for snnTorch;
  deprecated in favor of Tonic and kept for compatibility, import smoke, and
  local file handling only."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# spikevision

> [!WARNING]
> `snntorch.spikevision` is deprecated. For new neuromorphic dataset workflows, use [Tonic](https://github.com/neuromorphs/tonic). This sub-skill exists only for legacy compatibility, import/signature smoke, and local file handling.

## Covers
- Legacy dataset wrappers: `NMNIST`, `DVSGesture`, `SHD`
- Legacy base helpers: `NeuromorphicDataset`, `StandardTransform`
- Local transform helpers and file readers used by the legacy datasets
- Lightweight import/signature inspection without dataset downloads

## Does not cover
- Tonic-first workflows
- Training notebooks or model training recipes
- Plotting helpers
- NIR interoperability
- Real dataset downloads during extraction

## Routing rule
- If the request is for a modern neuromorphic pipeline, route to Tonic guidance first.
- If the request is to support, inspect, or migrate an old `spikevision` script, use the bundled references and the introspection helper.
- If the task would require fetching raw datasets from the network, stop and treat that as out of scope for extraction.

## Primary entry points
- Read `references/api-reference.md` for supported symbols, signatures, and on-disk expectations.
- Read `references/workflows.md` for safe legacy usage patterns.
- Read `references/troubleshooting.md` for dependency, layout, and constructor quirks.
- Run `scripts/spikevision_introspect.py` to confirm the deprecation warning, exposed classes, and safe transform constructors.

## Working constraints
- Keep this surface legacy-only.
- Prefer wrapper-level compatibility over adding new behavior.
- Keep dataset downloads and cache creation out of synthetic verification.
- Use the modern Tonic route whenever a user is starting fresh.
