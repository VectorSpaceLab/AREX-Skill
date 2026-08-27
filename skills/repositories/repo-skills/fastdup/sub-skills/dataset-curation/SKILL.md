---
name: dataset-curation
description: "Guide fastdup workflows for local image cleanup, duplicate
  removal, gallery generation, and binary feature round-trips."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# dataset-curation

Use this sub-skill for fastdup's core local-corpus workflows: duplicates, outliers, broken images, components, stats, and disk cleanup.

## Use when

The request mentions any of the following:

- cleaning a folder of images
- finding duplicates or near-duplicates
- spotting broken images or bad files
- generating duplicate, outlier, component, similarity, or stats galleries
- removing duplicates from disk
- working with `features.dat`, `features.dat.csv`, or binary feature round-trips
- using `fd.run(...)` or `fastdup.run(...)` on a plain image folder

## Typical workflow

1. Confirm the input is a local folder, file list, or a synthetic fixture.
2. Choose the run path:
   - `fastdup.create(...); fd.run(...)` for object-oriented use
   - `fastdup.run(...)` for one-shot use
   - `fastdup.remove_duplicates(...)` when the goal is cleanup
3. Set the analysis knobs that matter most:
   - `num_images` for smoke runs
   - `threshold` for similarity sensitivity
   - `lower_threshold` for outlier selection
   - `lazy_load` for large galleries
   - `distance` / `ccthreshold` when duplicate cleanup is the real goal
4. Inspect the galleries and CSV outputs.
5. If the workflow needs a tiny deterministic fixture, run the bundled synthetic-image script first.

## What to read

- `../../references/api-reference.md` for the main API and gallery methods
- `../../references/data-formats.md` for file names, output names, and feature-vector layout
- `../../references/workflows.md` for the core dataset-curation sequence
- `../../references/troubleshooting.md` for package-wide install/import and image-decoding issues
- `references/troubleshooting.md` in this sub-skill for local cleanup pitfalls

## Bundled scripts

Run these when you need a fast smoke check or a reproducible fixture:

- `../../scripts/make_synthetic_image_data.py` — create a small image corpus with valid, corrupted, duplicated, and missing rows
- `../../scripts/run_core_analysis_smoke.py` — run a full tiny analysis and generate galleries
- `../../scripts/run_feature_vector_smoke.py` — verify binary feature save/load round-trips

## Common decisions

- Use `remove_duplicates` only when deleting files from disk is the actual goal.
- Use `fastdup.run(..., num_images=...)` or `fd.run(..., num_images=...)` for smoke tests.
- Use `show=False` in gallery helpers when you only need file generation.
- Keep filenames aligned with the input folder layout; path mismatches are the most common failure mode.
- If a gallery returns no interesting pairs, lower the threshold or use a richer fixture.

## Outputs to expect

- `similarity.csv`
- `outliers.csv`
- `stats.csv`
- `component_info.csv`
- `connected_components.csv`
- HTML galleries under a `galleries/` directory

## Known limitation

The workflow assumes the package's core CPU path. GPU hardware is not required for the selected fastdup dataset-curation scope.
