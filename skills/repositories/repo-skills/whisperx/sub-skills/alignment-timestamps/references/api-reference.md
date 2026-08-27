# Alignment API reference

## Purpose

Read this when implementing WhisperX forced alignment in Python, validating aligned result schemas, or deciding whether to request word-level or character-level timestamps.

The facts here are distilled from package source and installed API inspection for `whisperx` 3.8.7rc1. They are self-contained so future agents do not need to reopen the source checkout.

## Public entry points

Installed top-level exports include lazy `whisperx.load_align_model(*args, **kwargs)` and `whisperx.align(*args, **kwargs)`. The detailed implementation signatures are:

```python
whisperx.alignment.load_align_model(
    language_code: str,
    device: str,
    model_name: str | None = None,
    model_dir=None,
    model_cache_only: bool = False,
)

whisperx.alignment.align(
    transcript,
    model,
    align_model_metadata: dict,
    audio,
    device: str,
    interpolate_method: str = "nearest",
    return_char_alignments: bool = False,
    print_progress: bool = False,
    combined_progress: bool = False,
    progress_callback=None,
) -> dict
```

### `load_align_model`

| Argument | Meaning | Practical guidance |
| --- | --- | --- |
| `language_code` | Language code used for default alignment model selection and sentence splitting. | Use the ASR result language for same-language transcription. Translation tasks cannot be aligned by the CLI because translated English text no longer matches the source speech. |
| `device` | Device string used when moving the alignment model. | Use the same available device style as the rest of the WhisperX workflow, for example `cpu` or `cuda`. CPU is valid but slower for real models. |
| `model_name` | Optional explicit model name. | Leave `None` to use WhisperX defaults. Pass a torchaudio pipeline name or Hugging Face wav2vec2 CTC model id when the language has no default or the default is not suitable. |
| `model_dir` | Optional cache directory passed to model loaders. | Use only for model cache control; do not bake local cache paths into reusable examples. |
| `model_cache_only` | Cache-only mode for Hugging Face model loading. | For Hugging Face models this becomes `local_files_only=True`. Torchaudio pipeline loading still depends on torchaudio's cache behavior. See troubleshooting before promising offline operation. |

Return value:

```python
align_model, align_metadata = whisperx.load_align_model(...)
```

`align_metadata` is a dictionary with:

| Key | Meaning |
| --- | --- |
| `language` | The `language_code` passed to `load_align_model`. |
| `dictionary` | Lower-cased CTC label/token dictionary used by `align`. Labels usually include a blank token such as `[pad]` or `<pad>` and may use `|` for spaces. |
| `type` | Either `torchaudio` or `huggingface`. `align` dispatches model calls based on this field. |

### `align`

| Argument | Meaning | Practical guidance |
| --- | --- | --- |
| `transcript` | Iterable/list of ASR segment dicts with `start`, `end`, `text`, and optional `avg_logprob`. | Pass `result["segments"]` from ASR. Prefer a concrete list because the implementation uses `len(transcript)`. |
| `model` | Alignment model returned by `load_align_model` or a compatible mocked model for tests. | Real workflows use wav2vec2 CTC models. Safe contract checks can mock a torchaudio-style model returning emissions. |
| `align_model_metadata` | Metadata from `load_align_model`. | Must contain `language`, `dictionary`, and `type`; language controls sentence splitting and whitespace handling. |
| `audio` | Audio path, NumPy array, or torch tensor. | A string path is loaded internally. Arrays/tensors should be mono 16 kHz-compatible with WhisperX audio conventions. |
| `device` | Device string for waveform/model calls. | Use `cpu` for safe checks; use `cuda` only when the installed stack and model cache support it. |
| `interpolate_method` | `nearest`, `linear`, or `ignore`. | Controls filling missing word and sentence timestamps. `ignore` preserves NaNs in the interpolation helper and can leave unaligned words without `start`/`end`. |
| `return_char_alignments` | Whether aligned segments include `chars`. | Use when JSON consumers need character timing. Most subtitle/file workflows need word timings instead. |
| `print_progress`, `combined_progress`, `progress_callback` | Progress reporting controls. | `progress_callback` receives percent complete during alignment. `combined_progress` is intended for a larger ASR+alignment progress display. |

`align` converts non-tensor audio to a tensor, slices each segment by `start`/`end`, runs the alignment model on each audio slice, performs CTC forced alignment, creates sentence-level aligned segments, interpolates missing timestamps, and returns a result dictionary.

## Input and output schemas

### Input ASR segment

```python
{
    "start": 0.0,
    "end": 5.0,
    "text": "cost 4,9 dollars",
    # optional
    "avg_logprob": -0.12,
}
```

### Aligned result

```python
{
    "segments": [
        {
            "start": 0.0,
            "end": 5.0,
            "text": "cost 4,9 dollars",
            "words": [
                {"word": "cost", "start": 0.12, "end": 0.40, "score": 0.98},
                {"word": "4,9", "start": 0.45, "end": 0.70, "score": 0.81},
                {"word": "dollars", "start": 0.76, "end": 1.20, "score": 0.95},
            ],
            # optional when requested and alignment succeeds
            "chars": [
                {"char": "c", "start": 0.12, "end": 0.16, "score": 0.99},
            ],
            # optional if present on input segment
            "avg_logprob": -0.12,
        }
    ],
    "word_segments": [
        {"word": "cost", "start": 0.12, "end": 0.40, "score": 0.98},
    ],
}
```

Typed schema facts:

| Schema name | Required fields | Notes |
| --- | --- | --- |
| `SingleSegment` | `start`, `end`, `text` | `avg_logprob` may be preserved. |
| `SingleWordSegment` | `word`, `start`, `end`, `score` | Runtime code can omit timing/score keys for unaligned words, so consumers should use `.get()` or check key presence. |
| `SingleCharSegment` | `char`, `start`, `end`, `score` | Runtime char dicts may omit timing/score keys when a character was not aligned. |
| `SingleAlignedSegment` | `start`, `end`, `text`, `words`, `chars` | `chars` is `None` unless `return_char_alignments=True`; unalignable fallback segments can have empty `words`. |
| `AlignedTranscriptionResult` | `segments`, `word_segments` | `word_segments` is the flattened concatenation of every segment's `words`. |

## Character and word construction details

- For languages with spaces, text is split into words on literal spaces and spaces are represented as `|` for CTC labels.
- For languages without spaces, currently Japanese (`ja`) and Chinese (`zh`), each character is treated like a word unit for alignment grouping.
- Leading and trailing spaces are ignored for clean-character alignment, but original text is preserved in output.
- Characters not found in the model dictionary and not whitespace are kept and routed through a wildcard CTC column. This is why digits and punctuation can receive timestamps in the current alignment path when the emission path supports them.
- If a segment has no usable characters, starts after the audio duration, or CTC backtracking fails, the function logs a warning and returns a fallback aligned segment with original segment boundaries and no word timestamps for that segment.

## CLI alignment flags backed by the same API

| CLI flag | API equivalent | Note |
| --- | --- | --- |
| `--align_model MODEL` | `load_align_model(..., model_name=MODEL)` | Use a torchaudio pipeline name or Hugging Face wav2vec2 CTC model id. |
| `--interpolate_method nearest|linear|ignore` | `align(..., interpolate_method=...)` | Controls timestamp filling for missing word/sentence times. |
| `--return_char_alignments` | `align(..., return_char_alignments=True)` | Character timestamps appear in JSON-style result dictionaries. |
| `--no_align` | skip `load_align_model` and `align` | Word-highlighting and word-based line options are incompatible with `--no_align`. |

## Validation checklist

Before using an aligned result downstream:

1. Confirm `aligned["segments"]` exists and every segment has `start`, `end`, `text`, and `words`.
2. Confirm required words have `start` and `end`; do not assume every word has timing when `interpolate_method="ignore"` or fallback alignment occurred.
3. Check monotonic timestamps for the words you will consume.
4. If producing subtitles or word highlighting, route file-format details to `outputs-subtitles` and validate fallback behavior for words without timing.
5. For regression-sensitive numeric text, run the bundled synthetic checker before relying on custom guidance.
