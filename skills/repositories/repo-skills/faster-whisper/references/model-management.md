# Model Management

## Purpose

Read this when the task involves choosing a model alias, downloading a model,
working offline, loading a local CTranslate2 model directory, or converting a
Whisper checkpoint before transcription.

## Model aliases

`available_models()` returned 19 aliases in the verified package:

- `tiny.en`, `tiny`
- `base.en`, `base`
- `small.en`, `small`
- `medium.en`, `medium`
- `large-v1`, `large-v2`, `large-v3`, `large`
- `distil-large-v2`
- `distil-medium.en`
- `distil-small.en`
- `distil-large-v3`
- `distil-large-v3.5`
- `large-v3-turbo`, `turbo`

Use the smallest model that fits the task and the host budget. For quick CPU
smoke checks, `tiny` is the usual first choice. For stronger accuracy or more
languages, use larger models as needed.

## Download behavior

```python
from faster_whisper import download_model

model_dir = download_model("tiny", cache_dir="/tmp/faster-whisper-cache")
```

`download_model(size_or_id, output_dir=None, local_files_only=False, cache_dir=None,
revision=None, use_auth_token=None)` resolves a public alias or Hugging Face
repository id and downloads the CTranslate2 model files needed by
`WhisperModel`.

Important behaviors:

- Aliases map to Systran or other published CTranslate2 Whisper repositories.
- If `local_files_only=True`, the cache must already contain the requested files.
- `output_dir` writes the downloaded snapshot to a chosen directory.
- `cache_dir` controls the Hugging Face cache location.

Required model files for local loading typically include `model.bin`,
`config.json`, `tokenizer.json`, and `preprocessor_config.json`.

## Local model directories

Use a local directory when a model has already been converted or cached:

```python
from faster_whisper import WhisperModel

model = WhisperModel(
    "/path/to/converted-ct2-whisper-model",
    device="cpu",
    compute_type="int8",
    local_files_only=True,
)
```

This is the right choice for offline environments, controlled deployments, and
fine-tuned models that were converted to the CTranslate2 layout.

## Conversion workflow

The repository documents converting a Transformers/OpenAI Whisper checkpoint to
CTranslate2 with `ct2-transformers-converter`.

Typical shape:

```bash
pip install transformers[torch]>=4.23
ct2-transformers-converter \
  --model openai/whisper-large-v3 \
  --output_dir whisper-large-v3-ct2 \
  --copy_files tokenizer.json preprocessor_config.json \
  --quantization float16
```

Use the root transcription workflow after conversion by pointing `WhisperModel`
at the output directory.

## Distil-Whisper notes

The README documents compatibility with Distil-Whisper checkpoints such as
`distil-large-v3`. Treat them as ordinary CTranslate2-compatible Whisper model
choices and prefer the same `WhisperModel` API.

## When to read troubleshooting instead

If model resolution fails, the issue is usually one of:

- network or cache access,
- an incorrect local CTranslate2 directory,
- an unsupported revision or repository id,
- or missing files after conversion.

In those cases, read the root troubleshooting file first and then the
transcription-specific troubleshooting file if the failure occurs during actual
inference.
