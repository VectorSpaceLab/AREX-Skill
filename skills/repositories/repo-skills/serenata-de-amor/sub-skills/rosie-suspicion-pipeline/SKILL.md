---
name: rosie-suspicion-pipeline
description: "Run, inspect, adapt, and troubleshoot Rosie's
  suspicious-reimbursement pipeline for Chamber of Deputies and Federal Senate
  data."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Rosie Suspicion Pipeline

Use this sub-skill when you need to run Rosie, inspect or adapt its suspicious-reimbursement pipeline, reason about classifier inputs/outputs, or debug why `suspicions.xz` or classifier model caches were not produced as expected.

## Start here

- For CLI commands, programmatic pipeline flow, `Core(settings, adapter)`, model-cache behavior, and safe offline adaptation, read [references/cli-and-workflows.md](references/cli-and-workflows.md).
- For classifier catalog entries, settings keys, required dataframe columns, and prediction semantics, read [references/classifier-reference.md](references/classifier-reference.md).
- For Chamber of Deputies and Federal Senate adapter normalization, expected input/output files, `suspicions.xz` shape, and download caveats, read [references/data-formats.md](references/data-formats.md).
- For dependency, data, legacy-library, cache, and network failure modes, read [references/troubleshooting.md](references/troubleshooting.md).
- To run a deterministic no-download smoke check for Core and any bundled classifier (default: invalid CNPJ/CPF), run [scripts/rosie_smoke.py](scripts/rosie_smoke.py).

## Fast routing

- **Run the native pipeline:** use `python rosie.py run chamber_of_deputies --output <directory>` or `python rosie.py run federal_senate --output <directory>` from a Rosie runtime checkout or container.
- **Run native tests:** use `python rosie.py test`, optionally followed by `core`, `chamber_of_deputies`, or `federal_senate`.
- **Avoid downloads or service starts:** do not call the native `run` command. Use a tiny dataframe and a classifier directly, or use `Core` with a custom adapter whose `dataset` and `path` are already local.
- **Understand a suspicious flag:** identify the classifier column in `suspicions.xz`, then use `classifier-reference.md` for required columns and true/false meaning.
- **Stale or surprising model output:** inspect/delete the classifier `.pkl` cache in the selected output directory, except for the monthly-subquota classifier, which is fitted every run and intentionally not cached.
- **Jarbas API questions:** route to the sibling `jarbas-data-api` sub-skill.
- **Data loading, Docker/services, deployment, or setup operations:** route to the sibling `deployment-and-data-ops` sub-skill.

## Operating boundaries

Rosie is the suspicion-generation application. It reads reimbursement datasets, normalizes them through the selected adapter, applies a settings-defined classifier catalog, and writes a compressed CSV named `suspicions.xz`. It does not serve the web API, run Jarbas, start databases, or load data into Jarbas by itself.

The native `run` workflow is not safe for offline-only checks because adapter access triggers data update/download routines. For deterministic local verification, use the bundled smoke script or construct a minimal dataframe for the specific classifier under inspection.

## Verification anchors

This sub-skill is grounded in the native CLI surface (`run`, `test`, module choices, and `--output`), `Core(settings, adapter)` behavior, Chamber/Federal adapter normalization, classifier docstrings and tests, model-cache tests, and installed API inspection for Rosie public classes and methods.
