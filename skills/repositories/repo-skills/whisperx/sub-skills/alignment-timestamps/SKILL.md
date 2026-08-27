---
name: alignment-timestamps
description: "Guides WhisperX forced alignment, multilingual alignment model
  selection, word and character timestamps, and timestamp interpolation
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 2-Clause
---

# Alignment timestamps

Use this sub-skill when a task needs WhisperX forced alignment after ASR: selecting a language-specific wav2vec2 alignment model, calling `load_align_model` and `align`, producing word or character timestamps, preserving timestamps for digits/symbols, or diagnosing why an aligned result lacks timing fields.

## Route here for

- Python alignment workflows that consume ASR `segments` and audio arrays/paths and return aligned `segments` plus `word_segments`.
- CLI/API choices for `--align_model`, `--interpolate_method`, and `--return_char_alignments`.
- Language-specific default alignment model selection, custom Hugging Face wav2vec2 model ids, and languages without whitespace-delimited words.
- Regression-backed guidance for unalignable characters such as digits, comma decimals, currency, and other symbols.

## Route elsewhere

- Initial ASR model loading, audio loading, batching, VAD, and transcription belong to sibling sub-skill `asr-python-api` or `transcription-cli`.
- Speaker diarization and speaker assignment belong to sibling sub-skill `diarization-speakers`.
- Subtitle/SRT/VTT/JSON rendering and writer options belong to sibling sub-skill `outputs-subtitles`.

## Read or run these bundled files

- Read [references/api-reference.md](references/api-reference.md) when writing Python code with `whisperx.load_align_model`, `whisperx.align`, alignment metadata, result schemas, progress callbacks, or char alignment options.
- Read [references/language-models.md](references/language-models.md) before choosing `language_code`, `--language`, `--align_model`, cache-only settings, a custom Hugging Face model, or when handling Japanese/Chinese text without spaces.
- Read [references/alignment-regressions.md](references/alignment-regressions.md) when timestamps are missing for digits, comma decimals such as `4,9`, mixed alphanumeric words, symbols, or when choosing `nearest`, `linear`, or `ignore` interpolation.
- Read [references/troubleshooting.md](references/troubleshooting.md) for failures involving unsupported languages, model cache/download errors, NLTK `punkt_tab`, empty segments, timestamps beyond the audio duration, char alignments, and languages without spaces.
- Run [scripts/check_alignment_contract.py](scripts/check_alignment_contract.py) for a safe CPU-only synthetic contract check that mocks a torchaudio-style alignment model and verifies a numeric comma word such as `4,9` receives timestamps without downloading any model.

## Minimal Python alignment shape

```python
import whisperx

# ASR result creation is owned by asr-python-api; alignment consumes its segments.
model_a, metadata = whisperx.load_align_model(
    language_code=result["language"],
    device="cpu",
    model_name=None,              # or a custom wav2vec2 model id/name
    model_dir=None,               # optional model cache directory
    model_cache_only=False,
)
aligned = whisperx.align(
    result["segments"],
    model_a,
    metadata,
    audio,
    device="cpu",
    interpolate_method="nearest", # nearest | linear | ignore
    return_char_alignments=False,
)
```

## Safe timestamp sanity check

```bash
python scripts/check_alignment_contract.py --help
python scripts/check_alignment_contract.py
python scripts/check_alignment_contract.py --interpolate-method ignore --text "halt mit 4,9 nicht ins parlament" --required-word "4,9" --language de
```

The helper is a bundled mock-contract check only. It does not validate real acoustic quality, does not download alignment models, and does not replace a real wav2vec2 alignment run when the downstream task requires production timestamps.
