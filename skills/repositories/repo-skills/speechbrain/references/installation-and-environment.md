# Installation and environment notes

Use this reference when a task starts with installing SpeechBrain, validating an environment, choosing CPU/GPU dependencies, or diagnosing optional integration imports.

## Package identity

- Distribution name: `speechbrain`
- Import module: `speechbrain`
- Source snapshot used for this skill reports package version `1.1.0`.
- Core dependencies include HyperPyYAML, NumPy, SciPy, SentencePiece, SoundFile, Torch, Torchaudio, tqdm, Requests, packaging, joblib, and Hugging Face Hub.
- The source checkout also uses additional development/recipe dependencies such as `pytest`, `ruff`, `yamllint`, `pandas`, `transformers`, and many recipe-specific `extra_requirements.txt` files.

## Basic installs

For package use:

```bash
pip install speechbrain
```

For local source development:

```bash
pip install -r requirements.txt
pip install --editable .
python -m pip check
```

If you only need a read-only import probe, avoid installing all recipe extras. Install the base package first, then add a recipe-specific `extra_requirements.txt` only for the selected recipe family.

## Minimal import probes

```bash
python - <<'PY'
import speechbrain as sb
print(sb.__version__)
print(sb.Brain)
from speechbrain.inference.ASR import EncoderASR, EncoderDecoderASR
from speechbrain.dataio import audio_io
print(EncoderASR, EncoderDecoderASR, audio_io.load)
PY
```

Run the bundled smoke script for a broader check:

```bash
python scripts/check_speechbrain_install.py --json
```

It checks package import, key inference/data/audio modules, `RunOptions`, and a synthetic audio I/O roundtrip without downloading models or datasets.

## Python, Torch, CPU, and CUDA

SpeechBrain is PyTorch-based. CPU environments are sufficient for imports, API inspection, audio I/O, small synthetic checks, and many tiny integration examples. Full training, large recipes, pretrained-model inference throughput, and multi-GPU work usually require a CUDA-capable PyTorch install and appropriate drivers.

Do not count `torch.cuda.is_available() == False` in a CPU wheel as a package failure unless the task explicitly requires CUDA. Conversely, do not treat a CPU smoke check as proof that a CUDA recipe, DDP launch, or profiling workload is verified.

Typical CPU PyTorch pinning pattern:

```bash
python -m pip install "torch==2.6.0+cpu" "torchaudio==2.6.0+cpu" \
  --extra-index-url https://download.pytorch.org/whl/cpu
```

For CUDA, choose the PyTorch wheel or Conda package that matches the host driver/toolkit policy, then run a real allocation probe:

```python
import torch
assert torch.cuda.is_available()
print(torch.cuda.get_device_name(0))
_ = torch.zeros(1, device="cuda")
```

## Hugging Face and network/cache behavior

Pretrained interfaces may fetch HyperPyYAML files, checkpoints, and optional Python modules from local folders, URLs, or Hugging Face repositories. Use `speechbrain.utils.fetching.FetchConfig` to control network and revisions. For reproducible or offline work, prefer a local model directory or pin a Hugging Face revision.

Example offline-protective pattern:

```python
from speechbrain.utils.fetching import FetchConfig, LocalStrategy
fetch_config = FetchConfig(allow_network=False)
# pass fetch_config=fetch_config and local_strategy=LocalStrategy.COPY or NO_LINK
```

Use `foreign_class` only for highly trusted sources because it fetches and executes external Python code.

## Audio backend

SpeechBrain now uses `speechbrain.dataio.audio_io`, a SoundFile-backed wrapper for `load`, `save`, and `info`. If audio loading fails:

1. Confirm `soundfile` imports.
2. Check the container format with `audio_io.info(path)`.
3. Prefer WAV or FLAC for troubleshooting.
4. Upgrade `soundfile` or install system `libsndfile` when the wheel lacks required codec support.
5. Convert unsupported codecs with external tools before passing them to SpeechBrain.

## Recipe-specific extras

Recipe dependencies are intentionally not installed globally. Look for the selected recipe family's `extra_requirements.txt` and install only that file. Common optional packages include `transformers`, `datasets`, `kenlm`, `k2`, `numba`, `librosa`, `pesq`, `pystoi`, `mir-eval`, `webdataset`, `scikit-learn`, `tensorboard`, and recipe-specific Git packages.

When a recipe points to a Git dependency, external dataset, Dropbox checkpoint, or pretrained Hugging Face model, treat installation and execution as networked side effects and ask for budget/approval before running it.
