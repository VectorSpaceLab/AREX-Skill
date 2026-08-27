---
name: model-sharing
description: "Prepare, inspect, and safely smoke-test Asteroid publishable
  models and upload metadata."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Model sharing and publishing

Use this sub-skill when the user wants to save a publishable Asteroid model, register an old sample rate, or prepare metadata for Zenodo upload.

## Typical triggers

- `save_publishable(...)`
- `upload_publishable(...)`
- `asteroid-upload`
- `asteroid-register-sr`
- Zenodo metadata, model cards, or publishable artifacts
- legacy checkpoints missing `sample_rate`

## What to do first

1. Confirm whether the user wants only a local publishable artifact or an actual upload.
2. Check whether the checkpoint already contains:
   - `model_args`
   - `state_dict`
   - `dataset`
   - `licenses`
   - `infos`
3. Determine whether a token or sandbox upload is involved.

## Standard workflow

- Read `references/publishable-models.md` for the local artifact contract.
- Read `references/cli-reference.md` for the public upload and sample-rate registration entrypoints.
- Read `references/troubleshooting.md` when the upload path is blocked by credentials or network dependencies.
- Use `scripts/smoke_publishable.py` for a safe local save/metadata smoke check.

## Safe boundaries

- Local `save_publishable(...)` smoke checks are fine.
- Real Zenodo uploads are credential-bound and should stay gated.
- Do not treat network upload as a default verification step.
- `asteroid-register-sr` is for legacy checkpoints that were saved before `sample_rate` was present.

## Useful inputs

- uploader name
- affiliation
- git username
- Zenodo token or sandbox token
- recipe name
- final metrics dict
- dataset/task/license metadata

## Troubleshooting reminders

- The model dict must include the required keys before saving or uploading.
- `upload_publishable(...)` needs a token unless one is present in `ACCESS_TOKEN`.
- `unit_test=True` is useful for safe metadata inspection, not a real upload.

## Inputs to inspect

- whether the user wants local artifact prep or a real publication step
- uploader name, affiliation, and git username
- whether a Zenodo token or sandbox token is available
- whether the checkpoint is a fresh model or a legacy checkpoint missing `sample_rate`

## Smoke sequence

1. Build a tiny model.
2. Serialize it.
3. Attach dataset and license metadata.
4. Save a publishable artifact in a temporary directory.
5. Inspect the generated `model.pth` without publishing it.

## What to avoid

- Do not make real publication the default path.
- Do not pretend that a missing token is a transient coding error.
- Do not claim the sample-rate registration helper is for modern checkpoints.
- Do not recommend network uploads when the user only needs a local smoke.

## Metadata reminders

- Required publishable keys must already be present in the model dict.
- The license list should come from the dataset or training source.
- The final metrics dict should be concrete, even for a smoke path.
- Recipe name and training config are part of the published metadata story.

## Good questions to ask when unclear

- Is this just a local publishable artifact or an actual upload?
- Do you have a token available?
- Is the checkpoint legacy or modern?
- What dataset/task name should appear in the metadata?
