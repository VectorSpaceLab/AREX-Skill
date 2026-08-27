---
name: fastdup
description: "Route fastdup workflows for visual dataset curation,
  annotation-driven analysis, embeddings and search, and video or exchange
  plumbing."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# fastdup

fastdup helps inspect visual datasets, surface duplicates and outliers, work with labeled image and object-detection data, reuse feature vectors, and generate galleries or exports from a completed run.

Use this repo skill when the task names fastdup directly or when the user asks about:

- duplicate, near-duplicate, outlier, broken-image, or mislabel discovery
- image-folder cleanup and connected-component summaries
- annotation-backed image classification or object detection workflows
- precomputed feature vectors, search, captions, OCR, or zero-shot enrichment
- video inputs, archives, cloud paths, or export helpers for CVAT / LabelImg

## Start here

1. Confirm the workflow family and open the matching sub-skill.
2. Read `references/data-formats.md` if you need filenames, dataframe columns, or output files.
3. Read `references/api-reference.md` for exact entry points and gallery helpers.
4. Read `references/troubleshooting.md` when the run depends on a platform package, optional model, or tricky input layout.
5. If the workflow is source-loader or export heavy, also read `references/source-loaders.md` or `references/exports.md`.
6. If you need a smoke helper, run the bundled script that matches the workflow family.

## Baseline usage

- Install the package with `pip install fastdup`.
- Verify the import with `python -c "import fastdup; print(fastdup.__version__)"`.
- Add workflow-specific extras only when the selected sub-skill needs them.
- The common object flow is `fd = fastdup.create(...)`, `fd.run(...)`, then `fd.vis.*`.
- The one-shot flow is `fastdup.run(...)`.
- The feature-vector flow uses `fastdup.save_binary_feature(...)`, `fastdup.load_binary_feature(...)`, and `fastdup.init_search(...)`.

## Sub-skills

### `dataset-curation`
Use for local visual cleanup, duplicate removal, outliers, connected components, gallery generation, and binary feature round-trips.

Read:
- `sub-skills/dataset-curation/SKILL.md`
- `references/workflows.md`
- `references/data-formats.md`
- `references/troubleshooting.md`

Run:
- `scripts/run_core_analysis_smoke.py`
- `scripts/run_feature_vector_smoke.py`
- `scripts/make_synthetic_image_data.py`

### `structured-datasets`
Use for labeled image classification, object detection, annotation dataframes, source loaders, and annotation-oriented exports.

Read:
- `sub-skills/structured-datasets/SKILL.md`
- `references/workflows.md`
- `references/data-formats.md`
- `references/source-loaders.md`
- `references/exports.md`
- `references/troubleshooting.md` for the known HF helper issue

Run:
- `scripts/run_labeled_classification_smoke.py`
- `scripts/run_labeled_detection_smoke.py`
- `scripts/make_synthetic_bbox_data.py`
- `scripts/export_cvat_smoke.py`
- `scripts/export_labelimg_smoke.py`

### `model-enrichment`
Use for embeddings, precomputed vectors, image search, captions, OCR, and zero-shot enrichment.

Read:
- `sub-skills/model-enrichment/SKILL.md`
- `references/api-reference.md`
- `references/workflows.md`
- `references/tensorboard-projector.md`

Run:
- `scripts/run_feature_vector_smoke.py`
- `scripts/run_search_smoke.py`
- `scripts/export_tensorboard_projector_smoke.py`

### `media-and-exchange`
Use for video inputs, tar/zip/webdataset plumbing, cloud path handling, and export helpers.

Read:
- `sub-skills/media-and-exchange/SKILL.md`
- `references/workflows.md`
- `references/exports.md`
- `references/troubleshooting.md`

Run:
- `scripts/export_cvat_smoke.py`
- `scripts/export_labelimg_smoke.py`

## Routing rule of thumb

- Start with `dataset-curation` when the task is about image quality or duplicate removal.
- Start with `structured-datasets` when the task already has annotations or a dataset source adapter.
- Start with `model-enrichment` when the task mentions feature vectors, captions, OCR, or search.
- Start with `media-and-exchange` when the task involves videos, archives, cloud paths, or export plumbing.

## Public metadata and staleness

- `references/repo-provenance.md` records the source commit, branch, dirty state, and evidence paths.
- `references/repo-routing-metadata.json` feeds the repo-skills router during import.
- If the package version or API surface changes, refresh this skill before relying on it for new work.
