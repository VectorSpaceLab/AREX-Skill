# PaddleGAN Repository Provenance

## Identity and baseline

- Upstream project: **PaddleGAN**
- Python distribution: `ppgan`
- Python import namespace: `ppgan`
- Skill baseline version: **2.1.0**
- Source commit: **`7d4c61f893fe7a094ff852e2b5a7353edbf24585`**

This fixed snapshot is the evidence baseline for the skill. The skill does not require, discover, or link to the source checkout at runtime; its runtime entry points are the bundled skill documents and helpers together with a separately installed `ppgan` environment.

## Evidence used to construct the skill

The baseline was distilled from these evidence categories:

1. Project overview and installation documentation, including the English and Chinese user guidance.
2. Model-family and workflow documentation for training, evaluation, applications, preprocessing, export, inference, and deployment.
3. YAML configuration examples covering model, dataset, optimizer, scheduler, metric, checkpoint, AMP, and distributed-training conventions.
4. The public `ppgan` package implementation, including application predictors, registries, builders, trainers, datasets, models, metrics, and utilities.
5. Repository command-line and application tooling used for training, evaluation, media workflows, data preparation, and model export.
6. Dataset, deployment, test, and TIPC materials used to confirm layouts, artifact conventions, backend boundaries, and failure modes.
7. Packaging and dependency manifests used to establish the `ppgan` identity, the 2.1.0 version baseline, and optional runtime requirements.

Evidence was used to document observable interfaces and operating constraints, not to make the local checkout a runtime dependency.

## Scope boundaries

### In scope

- Shared installation, configuration, and readiness checks.
- YAML-driven training, evaluation, resume/load, AMP, logging, and distributed-launch planning.
- Single-image, face, latent, video, motion, restoration, super-resolution, and lip-sync application workflows.
- Dataset layout, preprocessing, download planning, and `dataroot` validation.
- Checkpoint export, static-artifact inspection, and deployment planning for Paddle Inference, TensorRT, Serving, Lite, C++, and TIPC surfaces.
- Routing those tasks to the five bundled sub-skills while preserving their safety and prerequisite checks.

### Out of scope

- Maintaining, patching, or reproducing the PaddleGAN source repository.
- Claiming behavior from versions or commits newer than the recorded baseline without a refresh.
- Automatically downloading data or weights, running full training, executing heavy media inference, starting services, compiling native targets, or running benchmarks merely to answer or route a request.
- Treating optional GPU, ffmpeg, face-analysis, CLIP, TensorRT, Serving, Lite, or C++ dependencies as universally available.
- Providing exhaustive coverage of every experimental script or replacing upstream licensing, model-card, dataset, and deployment documentation.

## Refresh checklist

When refreshing the skill against a newer PaddleGAN snapshot:

- [ ] Confirm the upstream project is still PaddleGAN and the distribution/import identity remains `ppgan`.
- [ ] Record the exact source commit and the package version; do not silently retain the 2.1.0 baseline for newer evidence.
- [ ] Re-review all evidence categories above, including bilingual docs, configs, package APIs, tooling, deployment material, tests, and packaging manifests.
- [ ] Compare training/evaluation flags, config keys, registries, checkpoint semantics, predictor APIs, preprocessing layouts, export artifacts, and supported deployment backends.
- [ ] Revalidate optional dependencies, device assumptions, automatic-download behavior, and the boundaries around heavy or external operations.
- [ ] Audit the root route table and all five sub-skill responsibilities for overlap, gaps, renamed workflows, and stale model-family guidance.
- [ ] Verify every bundled helper and documented command against the refreshed interfaces using safe checks before considering heavyweight execution.
- [ ] Parse the routing metadata as JSON and confirm every route id is unique and every relative runtime path resolves to the intended `SKILL.md`.
- [ ] Update this record with the new baseline and evidence conclusions without adding runtime links to a source checkout.

