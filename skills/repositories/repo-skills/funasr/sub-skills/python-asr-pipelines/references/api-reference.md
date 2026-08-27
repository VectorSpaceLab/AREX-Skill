# API reference

This reference covers the installed Python ASR path: `import funasr`, `AutoModel`, audio-byte loading, timestamp helpers, hotword correction, and the lightweight CER/WER metric helper.

## Import and version

- `import funasr` works even before PyTorch is installed.
- `funasr.__version__` is available from the top-level package.
- `from funasr import AutoModel` requires PyTorch; the package raises a clear error if `torch` is missing.

## `AutoModel`

Constructor shape:

```python
from funasr import AutoModel

model = AutoModel(
    model="paraformer-zh",
    device="cpu",
    hub="ms",
    vad_model="fsmn-vad",
    vad_kwargs={"max_single_segment_time": 30000},
    punc_model="ct-punc",
    spk_model="cam++",
    ncpu=4,
    disable_update=True,
)
```

### Key arguments

| Argument | Meaning | Notes |
|---|---|---|
| `model` | Main ASR / utility model id or local path | Common choices here are SenseVoice and Paraformer family checkpoints. |
| `device` | `cuda:0`, `cpu`, `mps`, `xpu`, `npu`, etc. | Falls back to CPU if the requested backend is unavailable. |
| `hub` | `ms` or `hf` | ModelScope is the default. |
| `vad_model` | VAD model id | Enables long-audio segmentation. |
| `vad_kwargs` | VAD overrides | Example: `max_single_segment_time`. |
| `punc_model` | Punctuation model id | Optional. Needed for punctuation-aware sentence segmentation. |
| `spk_model` | Speaker model id | Requires `vad_model`; `cam++` is a common choice. |
| `spk_mode` | `default`, `vad_segment`, `punc_segment` | `punc_segment` expects punctuation/timestamp alignment. |
| `ncpu` | Torch thread count | Defaults to 4. |
| `disable_update` | Skip version check | Useful in controlled environments. |

### Construction behavior

- The package downloads model assets from the selected hub unless `model_conf` is already present.
- If the requested device is not available, construction falls back to CPU and uses batch size 1.
- `spk_model` implies speaker clustering support; `punc_segment` speaker routing needs punctuation or timestamp alignment.
- `punc_model=None` is valid, but sentence segmentation may be empty or may fall back to VAD-based segments.

## Input forms

`AutoModel.generate()` accepts more than one kind of input:

| Input form | Example | Notes |
|---|---|---|
| Local file path | `"audio.wav"` | Most common route. |
| URL | `"https://.../sample.wav"` | Downloaded first, then decoded. |
| Raw bytes | `audio_bytes` | `load_bytes()` can distinguish raw PCM from container audio. |
| `BytesIO` | `io.BytesIO(...)` | Useful for in-memory uploads. |
| Numpy array | `np.ndarray` | Interpreted as audio samples. |
| Torch tensor | `torch.Tensor` | Useful for batched or feature inputs. |
| List / tuple | `["a.wav", "b.wav"]` | Batch inference. |
| `wav.scp` / text / jsonl lists | file path | The helper reads per-line entries. |
| `kaldi_ark` | archive path | Supported by `load_audio_text_image_video()`. |

### Audio-byte helpers

- `load_audio_text_image_video()` loads local files, URLs, arrays, tensors, and lists.
- `load_bytes()` handles either raw `int16` PCM bytes or supported container audio bytes.
- Raw PCM is treated as signed 16-bit little-endian samples with no container header.
- Container bytes such as WAV, MP3, FLAC, OGG, MP4/M4A, and WebM are decoded through the installed audio backends.

## `generate()`

Signature shape:

```python
results = model.generate(input=..., input_len=None, progress_callback=None, **cfg)
```

Common runtime kwargs:

- `language`
- `cache`
- `batch_size_s`
- `batch_size_threshold_s`
- `is_final`
- `hotword` / `hotwords`
- `postprocess_hotwords`
- `postprocess_hotword_file`
- `postprocess_hotword_threshold`
- `return_postprocess_hotword_matches`
- `sentence_timestamp`
- `output_timestamp`
- `return_time_stamps`
- `return_raw_text`
- `return_spk_res`
- `use_itn`

### Result shape

A normal result is a list of dicts. Common fields include:

| Field | Meaning |
|---|---|
| `key` | Sample identifier. |
| `text` | Final transcript text. |
| `timestamp` / `timestamps` | Token- or character-level timing data. |
| `sentence_info` | Sentence segments with `text`, `start`, `end`, optional `spk`, and `timestamp`. |
| `raw_text` | Pre-cleanup text when requested. |
| `postprocess_hotword_matches` | Replacement details when requested. |
| `spk_embedding_center` | Optional per-speaker center embeddings. |

### Mode behavior

- Without `vad_model`, `generate()` runs single-utterance inference and then optionally reruns punctuation on the final text.
- With `vad_model`, `generate()` segments long audio, transcribes each VAD span, merges timestamps, and can build `sentence_info`.
- With `spk_model`, speaker clustering is added after ASR.
- `sentence_timestamp=True` asks for sentence-level segments even when no speaker model is used.

## Hotword correction

There are two different hotword paths:

1. **Model-level boosting** via `hotword` or `hotwords` during decoding.
2. **Text-level correction** via `postprocess_hotwords` after decoding.

`postprocess_hotwords` accepts:

- `str` with one item per line
- `list[str]`
- `dict[str, str]`

Explicit mappings can use `wrong=>right`, `wrong->right`, or `wrong→right`.

Fuzzy matching is optional. It requires `pypinyin` and `rapidfuzz`; explicit mappings work without them.

## Timestamp helpers

- `timestamp_sentence()` handles punctuation-aware sentence segmentation for Chinese-like spacing.
- `timestamp_sentence_en()` handles English-like spacing.
- Both produce `sentence_info`-style dicts.
- If punctuation alignment is unavailable, callers should fall back to VAD segment bounds or a single full-audio cue.

## Speaker verification and diarization

- A standalone speaker-verification model returns `spk_embedding`.
- In ASR + diarization mode, those embeddings are clustered and attached to sentence segments.
- `spk_model` requires `vad_model`; `punc_segment` routing also expects punctuation/timestamp alignment.

## Metrics helper

`funasr.metrics.common.ErrorCalculator` provides quick CER/WER calculations using `rapidfuzz.distance.Levenshtein`.
It returns `None` when the reference length is zero, which keeps empty-reference checks from crashing.

## See also

- `references/cli-reference.md`
- `references/workflows.md`
- `references/troubleshooting.md`
