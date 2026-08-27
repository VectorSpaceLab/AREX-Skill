# Python enhancement workflows

These workflows assume an installed DeepFilterNet Python environment. They are written to avoid any dependency on the original repository checkout.

## 1. Verify the package before using a model

Run this first for import or CLI problems:

```bash
python - <<'PY'
import importlib, inspect
import torch, torchaudio, libdf
import df
m = importlib.import_module("df.enhance")
print("df", getattr(df, "__version__", "unknown"))
print("torch", torch.__version__, "cuda", torch.cuda.is_available())
print("torchaudio", torchaudio.__version__)
print("pretrained", m.PRETRAINED_MODELS, "default", m.DEFAULT_MODEL)
print("init_df", inspect.signature(m.init_df))
print("enhance", inspect.signature(m.enhance))
PY

deepFilter --help >/dev/null
deep-filter-py --help >/dev/null
```

Expected result: no `ModuleNotFoundError`; constants list `DeepFilterNet`, `DeepFilterNet2`, `DeepFilterNet3`; default is `DeepFilterNet3`; both CLI help commands exit 0.

If this fails, use [troubleshooting](troubleshooting.md#install-and-import-failures) before loading a model.

## 2. No-network local model recipe

Use this when the environment cannot download model archives.

### Required local model layout

```text
local-model-dir/
  config.ini
  checkpoints/
    checkpoint files for best/latest/or integer epoch
```

### Check the directory without loading torch weights

```bash
python - <<'PY'
from pathlib import Path
model = Path("local-model-dir")
missing = []
if not model.is_dir():
    missing.append("model directory")
if not (model / "config.ini").is_file():
    missing.append("config.ini")
if not (model / "checkpoints").is_dir():
    missing.append("checkpoints/")
if missing:
    raise SystemExit("Missing: " + ", ".join(missing))
print("local model layout looks usable:", model)
PY
```

### Enhance one file with the bundled no-network-by-default helper

```bash
python sub-skills/python-enhancement/scripts/enhance_with_deepfilternet.py \
  --model-base-dir local-model-dir \
  --input-file noisy.wav \
  --output-file enhanced.wav
```

When running from inside this sub-skill directory, use:

```bash
python scripts/enhance_with_deepfilternet.py \
  --model-base-dir local-model-dir \
  --input-file noisy.wav \
  --output-file enhanced.wav
```

The helper refuses to download unless `--allow-download` is explicitly supplied. It also requires an explicit output path and will not overwrite it unless `--overwrite` is supplied.

### Force CPU for offline reproducibility

```bash
DEVICE=cpu python scripts/enhance_with_deepfilternet.py \
  --model-base-dir local-model-dir \
  --input-file noisy.wav \
  --output-file enhanced.wav
```

or:

```bash
python scripts/enhance_with_deepfilternet.py \
  --device cpu \
  --model-base-dir local-model-dir \
  --input-file noisy.wav \
  --output-file enhanced.wav
```

Stop if the model loader reports missing `config.ini`, missing checkpoints, or a checkpoint epoch that cannot be found. Do not switch to a pretrained model name in an offline task unless the cache is already populated.

## 3. Python API enhancement recipe

Use this for custom scripts, in-memory tensors, or when you need exact control over output naming.

```python
import importlib
from pathlib import Path
from df.io import load_audio, resample, save_audio

enhance_mod = importlib.import_module("df.enhance")
model_dir = Path("local-model-dir")
model, df_state, suffix, epoch = enhance_mod.init_df(
    model_base_dir=str(model_dir),
    post_filter=False,
    log_file=None,
)

audio, meta = load_audio("noisy.wav", sr=df_state.sr())
enhanced = enhance_mod.enhance(
    model,
    df_state,
    audio,
    pad=True,
    atten_lim_db=None,
)

out_sr = meta.sample_rate
if out_sr != df_state.sr():
    enhanced = resample(enhanced, df_state.sr(), out_sr)

save_audio("enhanced.wav", enhanced, sr=out_sr)
```

Options to add:

- Post-filter: `init_df(..., post_filter=True)`.
- Attenuation limit: `enhance(..., atten_lim_db=12)`.
- Disable delay compensation: `enhance(..., pad=False)`.
- Avoid model-directory log writes: keep `log_file=None`.
- Force CPU: set `DEVICE=cpu` before `init_df()`.

Validation after saving:

```bash
python - <<'PY'
import torchaudio
for f in ["noisy.wav", "enhanced.wav"]:
    info = torchaudio.info(f)
    print(f, "sr=", info.sample_rate, "frames=", info.num_frames, "channels=", info.num_channels)
PY
```

Expected: output sample rate matches the original input if you resampled back; output duration is close to the input duration when `pad=True`.

## 4. Installed CLI batch or directory enhancement

Use the installed CLI for simple batch work when output filenames can follow the package suffix policy.

```bash
mkdir -p enhanced_wavs

deepFilter \
  --model-base-dir local-model-dir \
  --output-dir enhanced_wavs \
  noisy1.wav noisy2.wav noisy3.wav
```

Directory form:

```bash
deepFilter \
  --model-base-dir local-model-dir \
  --noisy-dir noisy_wavs \
  --output-dir enhanced_wavs
```

Add controls as needed:

```bash
deepFilter \
  --model-base-dir local-model-dir \
  --pf \
  --atten-lim 12 \
  --no-suffix \
  --output-dir enhanced_wavs \
  noisy.wav
```

Stop conditions:

- Do not combine positional files with `--noisy-dir`.
- Do not use `--no-suffix` with an output directory that already contains same-named files unless overwriting is intended.
- If directory order or extension filtering matters, generate an explicit file list and call the CLI on those files.

## 5. Diagnose non-48 kHz audio before enhancement

The pretrained models are configured for 48 kHz model audio. The package can resample through `df.io.load_audio`, but diagnose unexpected inputs before blaming the model.

```bash
python - <<'PY'
import torchaudio
for path in ["noisy.wav"]:
    info = torchaudio.info(path)
    print(path, "sample_rate=", info.sample_rate, "channels=", info.num_channels, "frames=", info.num_frames)
    if info.sample_rate != 48000:
        print("  note: will be resampled to the model rate for enhancement")
PY
```

If resampling fails, install/repair `torchaudio` with audio backend support or convert the file to WAV/PCM with a trusted audio tool before retrying.

## 6. `libdf` no-network STFT/ERB smoke

Run the bundled smoke before using low-level primitives or when `ModuleNotFoundError: libdf` appears:

```bash
python scripts/libdf_smoke.py --sr 48000 --fft 960 --hop 480 --duration 0.1
```

Expected output includes:

- input shape `[1, samples]`;
- complex STFT shape `[1, frames, fft//2 + 1]`;
- synthesized audio shape `[1, samples]` for hop-aligned smoke inputs;
- ERB shape `[1, frames, nb_bands]`;
- finite `erb_norm` and `unit_norm` arrays.

This smoke does not load model checkpoints, audio files, or network resources.

## 7. Pretrained names versus local directories

Decision guide:

| Situation | Use |
|---|---|
| You have no network and a local extracted model | Pass the local directory to `--model-base-dir` or `init_df(model_base_dir=...)`. |
| You have no network but the model is already cached | Use the bundled helper without `--allow-download`; it accepts cached pretrained names after verifying local cache files. |
| You can allow package downloads | Use `deepFilter -m DeepFilterNet3 ...` or the helper with `--allow-download`. |
| You need exact reproducibility | Use a local model directory and record the model directory contents/checkpoint epoch outside the runtime skill. |
| You need ONNX or Rust model archives | Route to the export/evaluation or Rust realtime sibling skill. |

## 8. Choosing CPU or CUDA

DeepFilterNet's package device helper selects CUDA when PyTorch reports CUDA available and no `DEVICE` override is set. For deterministic troubleshooting:

```bash
DEVICE=cpu deepFilter --model-base-dir local-model-dir -o enhanced noisy.wav
```

For Python scripts:

```python
import os
os.environ["DEVICE"] = "cpu"  # set before init_df()
```

Use CUDA only after the CPU path works. A CPU-only PyTorch wheel cannot use GPU even on a GPU host; install a CUDA-matched PyTorch/torchaudio pair if acceleration is required.
