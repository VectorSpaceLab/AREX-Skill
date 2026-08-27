---
name: deep-filter-net
description: "Route DeepFilterNet speech enhancement, Python API/CLI, training
  data, model export/evaluation, and Rust/LADSPA realtime workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# DeepFilterNet repo skill

Use this skill when a task involves DeepFilterNet, DeepFilterNet2/3, deep filtering for speech/audio enhancement, the Python `deepFilter` CLI, `df.enhance` APIs, HDF5 training data, ONNX export/evaluation, or the Rust `deep-filter`/LADSPA realtime runtime.

## First route by task

- **Python enhancement and `libdf` primitives**: use [python-enhancement](sub-skills/python-enhancement/SKILL.md) for `deepFilter`, `deep-filter-py`, `df.enhance.init_df`, `df.enhance.enhance`, `df.io`, model directories, pretrained names, CPU/CUDA selection, and `libdf.DF` STFT/ERB smoke checks.
- **Training data and training setup**: use [training-data](sub-skills/training-data/SKILL.md) for HDF5 speech/noise/RIR datasets, `dataset.cfg`, `prepare_data`, `df.train`, `base_dir`, checkpoints/resume, and host-specific batch sizes.
- **Model export and evaluation**: use [model-export-evaluation](sub-skills/model-export-evaluation/SKILL.md) for ONNX export outputs, model summaries, VoiceBank/DNS2020 evaluation, DNSMOS, PESQ/STOI/composite metrics, and completed export directory validation.
- **Rust realtime deployment**: use [rust-realtime-deployment](sub-skills/rust-realtime-deployment/SKILL.md) for the native Rust `deep-filter` binary, model archives, LADSPA plugin builds, PipeWire virtual source/sink templates, tract/WASM notes, and demo/UI prerequisites.

## Confirm install and package surface

Read [installation-and-package-map](references/installation-and-package-map.md) before choosing extras or backend packages. For a safe no-network check from this skill directory:

```bash
python scripts/check_deepfilternet_install.py
```

The checker verifies required imports, `deepFilter`/`deep-filter-py --help`, and a tiny `libdf` STFT/ERB smoke test without downloading models, running training, building Rust, or touching audio services.

## DeepFilterNet essentials

- Python package import root: `df`.
- Main Python CLI entry points: `deepFilter` and `deep-filter-py`.
- Required low-level Python extension for enhancement: `libdf` from `deepfilterlib`.
- Optional training dataloader extension: `libdfdata` from `deepfilterdataloader`.
- Pretrained Python model names used by the package: `DeepFilterNet`, `DeepFilterNet2`, `DeepFilterNet3`; the source default is `DeepFilterNet3`.
- Python model audio is 48 kHz by default; the package can resample inputs but future agents should make sample-rate decisions explicit.
- CUDA is optional acceleration. CPU is enough for import/API/helper correctness checks unless the user specifically asks to verify GPU performance.
- Rust/LADSPA/PipeWire workflows are system-level: never install Rust packages, write `/etc`, restart PipeWire, or attach live audio devices without explicit user approval.

## Troubleshooting entry point

For cross-cutting failures, start with [references/troubleshooting.md](references/troubleshooting.md). Then move to the nearest sub-skill troubleshooting file for concrete recovery commands and stop conditions.

## Provenance and refresh

Read [repo-provenance](references/repo-provenance.md) before deciding whether this skill matches a current checkout. If the commit, package metadata, dirty state, source layout, or public entry points differ materially, refresh the repo skill.

Structured router metadata for managed repo-skill import is in [repo-routing-metadata.json](references/repo-routing-metadata.json). This production run intentionally leaves the skill as a self-contained repository artifact and does not import it into a live router.
