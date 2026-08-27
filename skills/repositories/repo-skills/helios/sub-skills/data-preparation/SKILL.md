---
name: data-preparation
description: "Route Helios dataset metadata, latent, and prompt-preparation workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Data preparation

Use this sub-skill when the user needs to prepare the data that Helios training
consumes or when they want to validate that a dataset matches the expected
layout before a distributed preprocessing job.

## Typical triggers

- "check my Helios JSON metadata"
- "prepare the training data"
- "validate the video list"
- "build latents"
- "prepare prompt embeddings"
- "make sure my dataset matches the toy format"

## What this sub-skill covers

- Metadata validation for the video/JSON format used by the toy examples.
- The expected naming convention for generated latent and embedding files.
- The relationship between clip metadata, frame counts, resolutions, and prompt
  strings.
- Preflight checks before the distributed GPU extraction jobs are launched.

## What it does not own

- The full Stage 1/2/3 training launch.
- Inference or demo generation.
- Metric evaluation and benchmarking.

## Read next

- `references/workflows.md` for the preparation sequence and file roles.
- `references/data-formats.md` for the JSON and `.pt` structures.
- `references/troubleshooting.md` for metadata and path-layout failures.
- `scripts/validate_toy_filter.py` for a bundled layout check.

## Working rule

Treat the heavy extraction jobs as environment-specific and cluster-specific.
This sub-skill focuses on the data contract and the validation layer that makes
those jobs safe to launch.
