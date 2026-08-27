---
name: python-enhancement
description: "Use DeepFilterNet's installed Python CLI/API for enhancement,
  model selection, audio I/O, and libdf STFT/ERB primitives."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Python enhancement

Use this sub-skill when the task is to enhance audio with the installed DeepFilterNet Python package, verify the Python install, choose or load a pretrained/local model, use the `df.enhance` API, perform audio I/O/resampling, or smoke-test `libdf` STFT/ISTFT/ERB primitives.

## Fast routing

- Use the installed Python CLI entry points `deepFilter` or `deep-filter-py` for ordinary file or directory enhancement. See [CLI reference](references/cli-reference.md).
- Use `df.enhance.init_df`, `df.enhance.enhance`, `df.io.load_audio`, `df.io.save_audio`, and `df.io.resample` for Python scripts. See [API reference](references/api-reference.md).
- Use [scripts/enhance_with_deepfilternet.py](scripts/enhance_with_deepfilternet.py) when you need an explicit no-network-by-default example that requires `--input-file` and `--output-file`.
- Use [scripts/libdf_smoke.py](scripts/libdf_smoke.py) to diagnose `libdf` install and STFT/ERB shape issues without loading a model or touching the network.
- For no-network model loading, local cache checks, batch/dir enhancement, package import checks, and API recipes, use [workflows](references/workflows.md).
- For failures, start with [troubleshooting](references/troubleshooting.md).

## Boundaries

This sub-skill owns Python enhancement and low-level `libdf` primitives only.

Route elsewhere:

- HDF5 dataset creation, dataset configs, and training loops: [training-data](../training-data/SKILL.md).
- ONNX export, objective evaluation, DNSMOS, PESQ/STOI metrics, and exported artifact validation: [model-export-evaluation](../model-export-evaluation/SKILL.md).
- Rust `deep-filter` binary, LADSPA, PipeWire, native realtime audio, and demo/UI workflows: [rust-realtime-deployment](../rust-realtime-deployment/SKILL.md).

## Required assumptions before enhancing

1. The package environment must import `torch`, `torchaudio`, `df`, and `libdf`.
2. DeepFilterNet model inference uses the model sample rate. The bundled pretrained models are configured for 48 kHz audio; load/resample inputs to the model sample rate before `enhance`.
3. Pretrained model names are `DeepFilterNet`, `DeepFilterNet2`, and `DeepFilterNet3`; package constants set the default model to `DeepFilterNet3`.
4. Passing a pretrained name to the package may download it when the cache is missing. For offline work, pass a local model directory containing `config.ini` and `checkpoints/`, or use the bundled helper script without `--allow-download`.
5. CPU is sufficient for correctness and small jobs. CUDA is optional acceleration; device selection defaults to CUDA when PyTorch reports it available unless the package config/environment forces CPU.

## Completion checks

A Python enhancement task is complete when:

- `deepFilter --help` or `deep-filter-py --help` works, or the Python import checks in [workflows](references/workflows.md) succeed.
- The selected model directory/name is resolved and its `config.ini` plus checkpoint directory are available.
- Input audio is loaded as `[channels, samples]`, resampled to the model sample rate if needed, enhanced, and saved to the requested output path or output directory.
- For `libdf` work, [scripts/libdf_smoke.py](scripts/libdf_smoke.py) reports finite STFT, synthesis, ERB, `erb_norm`, and `unit_norm` outputs with the expected shapes.
