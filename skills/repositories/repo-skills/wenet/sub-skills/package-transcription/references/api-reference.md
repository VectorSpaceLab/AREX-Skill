# WeNet Package API Reference

Read this when using WeNet through Python rather than a recipe or runtime
server.

## Public import surface

The package exposes three top-level helpers:

```python
from wenet import load_model, load_feature, load_tokenizer
```

Verified signatures:

```text
load_model(model_name_or_path, device='cpu')
load_feature(model_name_or_path)
load_tokenizer(model_name_or_path)
```

## Model names and local model directories

`model_name_or_path` can be either a built-in model key or a local model
directory. Built-in keys are routed through WeNet's model hub and may download
model archives before returning a directory. Useful public keys include:

- `wenetspeech`
- `paraformer`
- `firered`
- `sensevoice_small`
- `whisper-large-v3`
- `whisper-large-v3-turbo`
- `punc`

The hub also contains legacy misspelled `whiper-*` keys. Prefer the correctly
spelled Whisper keys unless you are matching an existing artifact.

A local model directory is expected to contain:

| File | Required | Purpose |
|---|---:|---|
| `train.yaml` | yes | model, tokenizer, feature, and dataset configuration |
| `final.pt` | yes | checkpoint loaded into the initialized model |
| `units.txt` | yes | token/unit vocabulary for the tokenizer |
| `global_cmvn` | no | cepstral mean/variance normalization stats used when present |

Run the bundled checker before calling `load_model()` on a local directory:

```bash
python sub-skills/package-transcription/scripts/check_wenet_package.py \
  --model-dir /path/to/model_dir --device cpu
```

## Loading and transcription

Basic Python pattern:

```python
import wenet

model = wenet.load_model("paraformer", device="cpu")
result = model.transcribe("audio.wav")
print(result.text)
```

Notes:

- Built-in model names can trigger network download and extraction. Use a local
  model directory when network access is not allowed.
- `load_model()` injects a tokenizer and feature function into the loaded model
  so `model.transcribe(audio_path)` can work with an audio file path.
- The public examples access `result.text`. Some older examples print
  dictionary-like fields; inspect the concrete result object when adapting old
  code.
- `load_feature()` returns `(compute_feature, feature_dim)`. The feature
  function decodes the wave file, resamples to 16 kHz, and computes the feature
  type configured in `train.yaml` (`fbank`, `mfcc`, or `log_mel_spectrogram`).
- `load_tokenizer()` rewrites tokenizer config paths to files inside the model
  directory when matching basenames exist.

## Device selection

`load_model(..., device='cpu')` moves the model to the requested device unless
the model is on a PyTorch `meta` device. Supported public device strings are
`cpu`, `cuda`, and `npu` in the package CLI/API surface.

Use `cpu` for deterministic checks. Use `cuda` only when PyTorch CUDA is
installed and `torch.cuda.is_available()` is true. Use `npu` only when the
Ascend CANN stack and `torch-npu` package are installed and compatible with the
PyTorch version.

## Safe validation checklist

Before transcription:

1. Import `wenet` and print the three helper signatures.
2. If using a local model directory, verify required files with the bundled
   checker.
3. If using a built-in model key, confirm network/model cache permission.
4. Check the requested backend; do not assume a visible GPU/NPU from the CLI
   flag alone.
5. Confirm the audio path exists and is readable.
