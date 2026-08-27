---
name: asteroid
description: "Route Asteroid tasks to the right sub-skill for pretrained
  inference, training recipes, custom model building, and model sharing."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Asteroid

Asteroid is a PyTorch audio source-separation toolkit for researchers. Use this repo skill when a task mentions Asteroid models, separation, enhancement, recipes, metrics, datasets, DSP blocks, or model sharing.

## Start here

Install the runtime from a clean environment, then read the sub-skill that matches the user intent.

From this skill directory, use the bundled `scripts/install_runtime.py` helper to bootstrap the public Asteroid runtime packages from the skill-local `scripts/runtime_requirements.txt` file without depending on the source checkout.

```bash
python scripts/install_runtime.py
python scripts/smoke_training.py --device cpu
```

If you want a tiny training sanity check after installation, run `scripts/smoke_training.py`.

If you only need a quick environment sanity check, read `references/installation.md`, `references/package-overview.md`, and `references/runtime-entrypoints.md`, then run the bundled `scripts/inspect_versions.py` helper.

## Route by task family

### Pretrained inference and separation
Read `sub-skills/pretrained-inference/SKILL.md` when the task is about:

- `asteroid-infer`
- `BaseModel.from_pretrained`
- `separate(...)`, `file_separate(...)`, `numpy_separate(...)`, `torch_separate(...)`
- Torch Hub or Hugging Face model loading
- `available_models()` or `show_available_models()`
- long-file overlap-add inference with `LambdaOverlapAdd`

This sub-skill covers loading pretrained checkpoints from local files, Zenodo URLs, and hub IDs, then separating audio tensors or files.

### Training recipes and evaluation
Read `sub-skills/training-recipes/SKILL.md` when the task is about:

- `System`, `Trainer`, optimizers, schedulers, or callbacks
- recipe `run.sh`, `train.py`, `eval.py`, `local/` data prep scripts, and stage-based experiment flows
- datasets such as `WhamDataset`, `LibriMix`, `Wsj0mixDataset`, `DNSDataset`, `MUSDB18Dataset`, `FUSSDataset`, `AVSpeechDataset`, `SmsWsjDataset`, or `KinectWsjMixDataset`
- losses and metrics such as `PITLossWrapper`, `SinkPITLossWrapper`, `MetricTracker`, or `get_metrics`

This sub-skill is the right entry point for dataset-backed training, evaluation, and recipe debugging. For a checkout-free training sanity check, use the bundled `scripts/smoke_training.py` entry point.

### Custom model building and core APIs
Read `sub-skills/custom-models/SKILL.md` when the task is about:

- `asteroid.models` constructors or custom subclasses of `BaseModel`
- filterbanks, encoders, decoders, or model registries
- mask blocks, recurrent blocks, normalization, complex-number helpers, or DSP modules
- shape, tracing, or serialization issues
- `asteroid.utils` parser helpers and other reusable building blocks

This sub-skill is the right place for new architectures, custom blocks, or low-level API inspection.

### Model sharing and publishing
Read `sub-skills/model-sharing/SKILL.md` when the task is about:

- `save_publishable(...)` or `upload_publishable(...)`
- `asteroid-upload` or `asteroid-register-sr`
- Zenodo metadata, model cards, or publishable artifacts
- sample-rate fixes for legacy checkpoints

This sub-skill covers preparing release-ready model artifacts and the safe local smoke checks around them.

## Common signals

Use the following as routing hints:

- `infer`, `separate`, `pretrained`, `hub`, `checkpoint`, `model list`, or `long file` → pretrained inference
- `train`, `evaluate`, `recipe`, `dataset`, `loss`, `metric`, `scheduler`, or `optimizer` → training recipes
- `filterbank`, `mask network`, `complex`, `beamforming`, `JIT`, `trace`, or `custom model` → custom model building
- `publish`, `upload`, `Zenodo`, `model card`, or `register sample rate` → model sharing

## Public package surfaces worth remembering

- `asteroid.models` exposes the ready-to-use model families and sharing helpers.
- `asteroid.data` exposes dataset loaders for the supported speech, music, and audio-visual corpora.
- `asteroid.losses` exposes PIT, MixIT, SinkPIT, SDR/MSE/STOI/PMSQE, and other loss helpers.
- `asteroid.metrics` exposes separation metrics and the `MetricTracker` helper.
- `asteroid.engine` exposes the Lightning `System` wrapper plus optimizer and scheduler helpers.
- `asteroid.dsp`, `asteroid.masknn`, `asteroid.complex_nn`, and `asteroid.utils` provide the reusable building blocks that custom-model tasks usually need.
- `scripts/install_runtime.py`, `scripts/smoke_training.py`, and `scripts/inspect_versions.py` provide self-contained runtime bootstrap and smoke-test entry points from the skill output.

## Read before editing or routing

- `references/repo-provenance.md` for the source snapshot.
- `references/repo-routing-metadata.json` for router placement.
- `references/troubleshooting.md` for cross-cutting failures.
