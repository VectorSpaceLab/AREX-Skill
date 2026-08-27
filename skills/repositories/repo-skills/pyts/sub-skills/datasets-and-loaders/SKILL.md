---
name: datasets-and-loaders
description: "Routes pyts dataset loading, cached toy datasets, synthetic
  generators, and UCR/UEA fetch workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# datasets-and-loaders

Use this sub-skill when a user asks how to load, inspect, fetch, or generate
pyts time-series datasets.

## What this covers

- Packaged toy loaders: `load_basic_motions`, `load_coffee`, `load_gunpoint`,
  `load_pig_central_venous_pressure`.
- Synthetic generation: `make_cylinder_bell_funnel`.
- Metadata and catalog helpers: `ucr_dataset_list`, `ucr_dataset_info`,
  `uea_dataset_list`, `uea_dataset_info`.
- Network-backed fetch helpers: `fetch_ucr_dataset`, `fetch_uea_dataset`.
- Shape, split, and cached-data expectations for downstream preprocessing,
  metrics, and classifier workflows.

## What this excludes

- Preprocessing and symbolic transforms: use
  `../preprocessing-and-symbols/SKILL.md`.
- Feature extraction, images, and decomposition: use
  `../feature-extraction-and-images/SKILL.md`.
- Metrics and classifiers: use `../metrics-and-classifiers/SKILL.md`.
- Multivariate wrappers: use `../multivariate-workflows/SKILL.md`.

## Start here

1. Read `references/workflows.md` for the supported dataset-loading patterns.
2. Read `references/data-formats.md` when you need shapes, split structure,
   or dataset catalog facts.
3. Read `references/troubleshooting.md` for network, cache, and naming errors.
4. Run `scripts/smoke.py` from this sub-skill directory to confirm the installed
   package can load the bundled datasets.

## Useful triggers

- "load GunPoint"
- "fetch UCR dataset metadata"
- "make a synthetic cylinder-bell-funnel dataset"
- "what shape does BasicMotions return?"
- "does pyts need network access for dataset helpers?"

## Routing hints

- If the user needs a dataset before scaling, discretizing, or modeling, stay
  here only long enough to identify the dataset shape and then route to the
  downstream workflow.
- If the user only needs network-free toy data for a smoke test, prefer the
  packaged loaders and `make_cylinder_bell_funnel`.
- If the user needs remote downloads, explain the cache and network dependency
  before promising a reproducible result.

## Links

- Read `references/workflows.md` for example loader calls and return shapes.
- Read `references/data-formats.md` for bundled dataset layouts and return
  conventions.
- Read `references/troubleshooting.md` when a loader name, cache path, or
  network fetch fails.
- Run `scripts/smoke.py` when you want a quick installed-package check.
