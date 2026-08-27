# Python enhancement troubleshooting

Use this when the Python CLI/API, local model loading, audio I/O, device selection, or `libdf` primitives fail.

## Install and import failures

### `ModuleNotFoundError: No module named 'df'`

Meaning: the DeepFilterNet Python package is not installed in the active environment.

Checks:

```bash
python -m pip show DeepFilterNet deepfilternet || true
python - <<'PY'
try:
    import df
    print("df ok", getattr(df, "__version__", "unknown"))
except Exception as exc:
    print(type(exc).__name__, exc)
    raise
PY
```

Fix:

```bash
python -m pip install deepfilternet
```

Then install a matching PyTorch/torchaudio pair if pip did not provide one appropriate for your platform.

### `ModuleNotFoundError: No module named 'libdf'`

Meaning: the Rust-backed Python extension from DeepFilterLib is missing or incompatible.

Checks:

```bash
python -m pip show DeepFilterLib deepfilterlib || true
python scripts/libdf_smoke.py --sr 16000 --fft 320 --hop 160 --duration 0.1
```

Fix:

```bash
python -m pip install deepfilterlib
```

Stop if no compatible wheel exists for the platform and no Rust build toolchain is available. Building the Rust extension is outside this Python enhancement sub-skill; treat it as an environment preparation problem.

### `ModuleNotFoundError: No module named 'torch'` or `torchaudio`

Meaning: the package installed without a working PyTorch audio stack.

CPU fix example:

```bash
python -m pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
```

CUDA fix: install the PyTorch and torchaudio wheels that match the target CUDA runtime. Verify with:

```bash
python - <<'PY'
import torch, torchaudio
print("torch", torch.__version__)
print("torchaudio", torchaudio.__version__)
print("cuda available", torch.cuda.is_available())
PY
```

If torchaudio imports but cannot load/save a file, see [Audio backend/load/save failures](#audio-backendloadsave-failures).

## CLI entry point failures

### `deepFilter: command not found`

Meaning: the scripts directory for the active Python environment is not on `PATH`, or DeepFilterNet is not installed there.

Checks:

```bash
python -m pip show DeepFilterNet deepfilternet || true
python - <<'PY'
import importlib.metadata as md
for dist in ["DeepFilterNet", "deepfilternet"]:
    try:
        print(dist, md.version(dist))
    except md.PackageNotFoundError:
        pass
PY
```

Workaround:

```bash
python -m df.enhance --help
```

If module execution is not packaged, invoke the installed script after activating the correct environment or reinstall the package.

### Python `deepFilter` versus Rust `deep-filter`

This sub-skill covers `deepFilter` and `deep-filter-py`. If the command is `deep-filter` with a hyphen and no `py`, route to [rust-realtime-deployment](../../rust-realtime-deployment/SKILL.md).

## Model cache and offline failures

### Pretrained name tries to download in an offline environment

Cause: `init_df(None)` or `init_df("DeepFilterNet3")` resolves through the DeepFilterNet user cache and downloads the model archive if missing.

No-network fixes:

1. Use a local extracted model directory:

   ```bash
   deepFilter --model-base-dir local-model-dir -o enhanced noisy.wav
   ```

2. Or use the bundled helper, which refuses downloads by default:

   ```bash
   python scripts/enhance_with_deepfilternet.py \
     --model-base-dir local-model-dir \
     --input-file noisy.wav \
     --output-file enhanced.wav
   ```

3. If using a cached pretrained name, first verify local cache presence with the helper. It will fail with an explicit message if the cache does not contain `config.ini` and `checkpoints/`.

Only pass `--allow-download` to the helper when network access is intentionally allowed.

### `NotADirectoryError: Base directory not found`

Cause: `--model-base-dir` points to a missing path or an unrecognized model name/path.

Fix checklist:

```bash
python - <<'PY'
from pathlib import Path
p = Path("local-model-dir")
print("exists", p.exists(), "is_dir", p.is_dir())
print("config", (p / "config.ini").is_file())
print("checkpoints", (p / "checkpoints").is_dir())
PY
```

Use the extracted model directory, not a zip/tar archive, for Python `init_df()`.

### `No config file found` or config value errors

Cause: `config.ini` is missing, unreadable, or not compatible with the installed DeepFilterNet code.

Fix:

- Confirm `local-model-dir/config.ini` exists.
- Confirm the model directory and code version are compatible.
- If this is a training output directory, make sure training wrote the expected config and checkpoint structure. Route training/checkpoint layout questions to [training-data](../../training-data/SKILL.md).

### `Could not find a checkpoint`

Cause: the `checkpoints/` directory does not contain the requested `best`, `latest`, or integer epoch checkpoint.

Fix:

```bash
deepFilter --model-base-dir local-model-dir --epoch latest -o enhanced noisy.wav
# or choose a known integer epoch:
deepFilter --model-base-dir local-model-dir --epoch 42 -o enhanced noisy.wav
```

If the directory only contains exported ONNX files, route to [model-export-evaluation](../../model-export-evaluation/SKILL.md); Python enhancement expects PyTorch checkpoint files.

## CPU vs CUDA device surprises

### CUDA is selected but fails

Cause: the package selects `cuda:0` when `torch.cuda.is_available()` is true and no `DEVICE` override is set.

Force CPU before model initialization:

```bash
DEVICE=cpu deepFilter --model-base-dir local-model-dir -o enhanced noisy.wav
```

or in Python:

```python
import os
os.environ["DEVICE"] = "cpu"  # before init_df()
```

With the bundled helper:

```bash
python scripts/enhance_with_deepfilternet.py \
  --device cpu \
  --model-base-dir local-model-dir \
  --input-file noisy.wav \
  --output-file enhanced.wav
```

### CUDA is expected but CPU is used

Checks:

```bash
python - <<'PY'
import torch
print("torch", torch.__version__)
print("cuda available", torch.cuda.is_available())
print("cuda version", torch.version.cuda)
PY
```

Fix: install a CUDA-enabled PyTorch and matching torchaudio build. Do not claim CUDA acceleration until the above check reports CUDA available and a small CPU-equivalent enhancement succeeds.

## Non-48 kHz inputs and resampling

The pretrained models are configured for 48 kHz model audio. The Python CLI and `df.io.load_audio(file, sr=df_state.sr())` resample nonmatching inputs to the model rate for inference.

Diagnose input:

```bash
python - <<'PY'
import torchaudio
info = torchaudio.info("noisy.wav")
print("sample_rate", info.sample_rate, "channels", info.num_channels, "frames", info.num_frames)
PY
```

Expected behavior:

- Native CLI: resamples to model rate, enhances, then resamples back to original sample rate before saving.
- `df.enhance.enhance`: assumes the tensor already matches `df_state.sr()`; it does not inspect sample rate.
- Bundled helper: mirrors CLI behavior and reports original/model/output sample rates.

Stop and convert/re-encode input if torchaudio cannot load it or if repeated resampling artifacts are unacceptable for the task.

## Audio backend/load/save failures

Symptoms:

- `torchaudio.info` or `torchaudio.load` cannot identify the input.
- `torchaudio.save` fails for the output extension or dtype.
- Multi-channel or unusual codec files produce unexpected shapes.

Checks:

```bash
python - <<'PY'
import torchaudio
for path in ["noisy.wav"]:
    print(path, torchaudio.info(path))
PY
```

Fixes:

- Prefer PCM WAV for first-pass troubleshooting.
- Ensure output parent directory exists.
- Try saving with `.wav` extension before more exotic formats.
- In custom API scripts, keep tensors shaped `[channels, samples]`.
- If the file loads as integer or has clipped amplitude, convert to normalized float before custom processing; `df.io.load_audio` normally returns floating tensors from torchaudio.

## Post-filter, attenuation, delay, and suffix confusion

### Post-filter (`--pf` / `post_filter=True`)

- Enables extra mask post-filtering for very noisy sections.
- Adds `_pf` to the model suffix used by the CLI.
- Can make speech sound more aggressively denoised; compare with and without for quality-sensitive tasks.

### Attenuation limit (`--atten-lim` / `atten_lim_db`)

- Limits maximum attenuation by mixing enhanced and noisy spectra.
- Example: `--atten-lim 12` keeps more background than unlimited suppression.
- Use when full suppression sounds unnatural or damages speech.

### Delay compensation

- Default CLI and helper behavior compensates STFT/model delay.
- `--no-delay-compensation` or `pad=False` can yield shorter/delayed output.
- Use the no-delay mode only for low-level streaming comparisons, not ordinary saved audio.

### Output suffix

- CLI default adds `<model_suffix>` to the basename; post-filter adds `_pf`.
- `--no-suffix` disables suffixing and can overwrite same-named files in the output directory.
- The bundled helper uses an explicit `--output-file` and does not suffix unless you choose the output name yourself.

## `libdf` primitive failures

Run:

```bash
python scripts/libdf_smoke.py --sr 48000 --fft 960 --hop 480 --duration 0.1
```

Common causes:

| Symptom | Likely cause | Action |
|---|---|---|
| `ModuleNotFoundError: libdf` | DeepFilterLib not installed. | Install `deepfilterlib` or use an environment prepared with the package extension. |
| Constructor error | Invalid `sr`, `fft`, `hop`, or band count. | Use positive integers; `hop` should be less than or equal to `fft`; start with `48000/960/480/32`. |
| Shape assertion fails | Unexpected wheel/API version. | Record actual shapes; do not proceed with hard-coded model feature shapes until reconciled. |
| Non-finite output | Bad input values or extension bug. | Retry with zero/sine smoke; reinstall compatible `deepfilterlib` if still failing. |

## When to stop and route elsewhere

- Need to create HDF5 datasets or train/fine-tune: [training-data](../../training-data/SKILL.md).
- Need ONNX export, ONNX runtime comparison, objective metrics, DNSMOS, PESQ, or STOI: [model-export-evaluation](../../model-export-evaluation/SKILL.md).
- Need Rust `deep-filter`, LADSPA, PipeWire virtual microphone/sink, or realtime demo: [rust-realtime-deployment](../../rust-realtime-deployment/SKILL.md).
