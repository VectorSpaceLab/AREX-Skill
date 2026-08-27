# Installation and Package Map

## When to read

Read this reference before choosing a DeepFilterNet install path, deciding whether a task belongs to Python or Rust runtime, or diagnosing missing optional dependencies.

## Package and import names

| Distribution/package | Import or executable | Purpose | Notes |
|---|---|---|---|
| `deepfilternet` / `DeepFilterNet` | `df`, `deepFilter`, `deep-filter-py` | Main Python speech-enhancement package, training code, CLI entry points | The package metadata exposes console scripts `deepFilter` and `deep-filter-py`. The source version in this skill snapshot is `0.5.7-pre`/normalized `0.5.7rc0`. |
| `deepfilterlib` / `DeepFilterLib` | `libdf` | Rust-backed Python extension for STFT/ISTFT, ERB features, and normalization primitives | Required by Python enhancement. If `ModuleNotFoundError: libdf` appears, reinstall the package or wheel for the active Python version. |
| `deepfilterdataloader` / `DeepFilterDataLoader` | `libdfdata` | Optional Rust-backed dataloader used by training | Required for full native `df.train` execution; may need HDF5 build/runtime libraries or a package wheel. |
| PyTorch + Torchaudio | `torch`, `torchaudio` | Model inference, audio load/save/resampling, training | Install a CPU or CUDA build deliberately. CUDA is acceleration, not required for small correctness checks. |
| `h5py`, audio codec support | `h5py`, torchaudio backends | HDF5 dataset preparation and validation | Needed for data conversion and deep HDF5 inspection, not for basic CLI help. |
| `onnx`, `onnxruntime`, `onnxsim`, `monkeytype` | optional modules | ONNX export and checking | Only needed for export workflows; the bundled export validator does not import ONNX. |
| `pystoi`, `pesq`, `scipy`, DNSMOS dependencies | optional modules/services | Objective evaluation and DNSMOS | Some DNSMOS paths need network downloads or API credentials. |
| Rust/Cargo workspace | `deep-filter` binary, `libdeep_filter_ladspa.so` | Native realtime/offline Rust runtime and LADSPA plugin | Build or use release artifacts outside the Python package flow. |

## Python install patterns

Use a clean environment and install the PyTorch/Torchaudio variant first when possible:

```bash
# CPU-oriented example; choose CUDA wheels only when GPU acceleration is required.
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install deepfilternet
```

For training workflows, install the training extra or otherwise ensure `libdfdata`/`deepfilterdataloader` is available:

```bash
pip install 'deepfilternet[train]'
```

For evaluation/export extras, install only what the selected workflow needs:

```bash
pip install 'deepfilternet[eval]'
pip install onnx onnxruntime onnxsim MonkeyType
```

Do not install every optional group unless the user explicitly needs training, export, and benchmark/DNSMOS workflows in one environment.

## CPU, CUDA, and device selection

DeepFilterNet correctness checks can run on CPU. CUDA is useful for speed, larger batch inference, and training, but the Python package chooses CUDA automatically when PyTorch reports it available unless the package configuration/environment selects CPU.

Use CPU deliberately when debugging reproducibility or avoiding GPU memory issues:

```bash
DEVICE=cpu deepFilter --model-base-dir /path/to/model path/to/noisy.wav
```

Before claiming CUDA support, run an environment-specific PyTorch CUDA smoke check and then a tiny DeepFilterNet model/load smoke with an approved model path. Do not treat a CPU install as CUDA verification.

## Runtime route by task

- Use [python-enhancement](../sub-skills/python-enhancement/SKILL.md) for Python `deepFilter`, `df.enhance`, audio files, pretrained/local model directories, and `libdf` primitives.
- Use [training-data](../sub-skills/training-data/SKILL.md) for HDF5 manifests, `dataset.cfg`, `prepare_data`, training setup, and checkpoint/base-dir behavior.
- Use [model-export-evaluation](../sub-skills/model-export-evaluation/SKILL.md) for ONNX export artifacts, objective metrics, DNSMOS, and model summaries.
- Use [rust-realtime-deployment](../sub-skills/rust-realtime-deployment/SKILL.md) for Rust `deep-filter`, model archives for tract/runtime, LADSPA, PipeWire, and realtime audio.

## Safe install verification

Run the root bundled checker from the generated skill directory:

```bash
python scripts/check_deepfilternet_install.py
python scripts/check_deepfilternet_install.py --json
```

The checker imports required modules, probes `deepFilter`/`deep-filter-py --help`, and runs a tiny no-network `libdf` smoke test. It does not download models, build Rust crates, open audio devices, or run training.

## Optional dependency stop conditions

Stop and ask for the missing dependency or permission when:

- a task requires model download but network access is not approved;
- a training run needs `libdfdata` or HDF5 support that is not installed;
- an export run needs ONNX dependencies or a local checkpoint/config;
- a DNSMOS run needs API credentials, local ONNX assets, or benchmark datasets;
- a Rust/LADSPA task needs Cargo, system packages, or PipeWire service changes.
