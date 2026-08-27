# Diarization API reference

This reference covers the WhisperX 3.8.7rc1 diarization surface used for speaker labels. It distinguishes model-backed diarization from safe assignment of existing diarization intervals.

## Imports

```python
import whisperx
from whisperx.diarize import DiarizationPipeline, assign_word_speakers, IntervalTree, Segment
```

`whisperx.assign_word_speakers(...)` is also exposed as a lazy top-level convenience wrapper around `whisperx.diarize.assign_word_speakers(...)`.

## `DiarizationPipeline`

Use `DiarizationPipeline` only when the task intentionally runs a pyannote speaker diarization model. Instantiating it calls pyannote model loading and can require network/cache access plus a Hugging Face token for gated models.

### Constructor

```python
DiarizationPipeline(model_name=None, token=None, device="cpu", cache_dir=None)
```

| Parameter | Meaning |
| --- | --- |
| `model_name` | Hugging Face model id or local/cache model reference. `None` selects `pyannote/speaker-diarization-community-1`. |
| `token` | Hugging Face access token passed to pyannote. Keep it secret; do not log or commit it. |
| `device` | PyTorch device string or `torch.device`, such as `"cpu"` or `"cuda"`. |
| `cache_dir` | Optional model cache directory passed through to pyannote loading. |

### Call

```python
diarize_segments = diarize_model(audio, min_speakers=None, max_speakers=None)
# or, with embeddings:
diarize_segments, speaker_embeddings = diarize_model(audio, return_embeddings=True)
```

Installed signature:

```python
DiarizationPipeline.__call__(
    audio,
    num_speakers=None,
    min_speakers=None,
    max_speakers=None,
    return_embeddings=False,
    progress_callback=None,
)
```

| Parameter | Meaning |
| --- | --- |
| `audio` | Audio path string or a NumPy waveform array. Path strings are loaded through WhisperX audio loading at the package sample rate. |
| `num_speakers` | Exact number of speakers, available in the Python API. |
| `min_speakers` / `max_speakers` | Bounds for pyannote speaker estimation. Use both equal to emulate an exact count from the CLI. |
| `return_embeddings` | When true, returns `(diarization_dataframe, speaker_embeddings_or_None)` instead of only the DataFrame. |
| `progress_callback` | Optional callable receiving percentage floats from 0 to 100. |

### Return data

Without embeddings, the call returns a `pandas.DataFrame` with at least:

| Column | Meaning |
| --- | --- |
| `segment` | Pyannote segment object. |
| `label` | Pyannote track label. |
| `speaker` | Speaker id string such as `SPEAKER_00`. |
| `start` | Segment start time in seconds. |
| `end` | Segment end time in seconds. |

With `return_embeddings=True`, the first return value is the same DataFrame and the second is either a dictionary mapping speaker ids to embedding vectors or `None` when pyannote did not provide embeddings.

## `assign_word_speakers`

Use this function when diarization intervals already exist and the goal is to add speaker labels to transcript segments/words. It does not instantiate pyannote and does not need a Hugging Face token.

```python
assign_word_speakers(
    diarize_df,
    transcript_result,
    speaker_embeddings=None,
    fill_nearest=False,
)
```

Installed signature:

```python
assign_word_speakers(
    diarize_df: pandas.DataFrame,
    transcript_result,
    speaker_embeddings=None,
    fill_nearest=False,
)
```

| Input | Contract |
| --- | --- |
| `diarize_df` | DataFrame containing numeric `start`, numeric `end`, and `speaker` columns. Extra pyannote columns are allowed. |
| `transcript_result` | WhisperX transcription or aligned transcription result dictionary with a top-level `segments` list. |
| `speaker_embeddings` | Optional `{speaker_id: embedding_vector}` dictionary. If supplied, it is attached to the result as top-level `speaker_embeddings`. |
| `fill_nearest` | If false, only direct time overlaps receive labels. If true, segments/words without overlap receive the nearest diarization speaker by interval midpoint. |

Assignment behavior:

1. If there are no transcript segments or the diarization DataFrame is empty, the input transcript is returned unchanged.
2. Diarization intervals are indexed by `IntervalTree`.
3. For each transcript segment, overlapping diarization intervals are queried and the speaker with the largest total intersection duration wins.
4. For each word with a `start` timestamp, the same dominant-overlap rule is applied. A missing word `end` defaults to the word start time.
5. When no overlap exists and `fill_nearest=True`, the nearest diarization interval midpoint supplies the speaker.
6. The function mutates the transcript dictionary and also returns it.

## `IntervalTree`

`IntervalTree(intervals)` is the fast overlap helper used by `assign_word_speakers`.

```python
tree = IntervalTree([(0.0, 1.2, "SPEAKER_00"), (1.2, 2.0, "SPEAKER_01")])
tree.query(0.4, 0.9)      # [("SPEAKER_00", 0.5)]
tree.find_nearest(1.9)    # "SPEAKER_01"
```

Use it for diagnostics or tests when explaining overlap/nearest-speaker behavior. Prefer `assign_word_speakers` for normal transcript mutation.

## `Segment`

`Segment(start, end, speaker=None)` is a small container with `.start`, `.end`, and `.speaker` attributes. It is not required for the DataFrame-based assignment workflow.

## CLI diarization flags

The `whisperx` CLI performs ASR/alignment first, then, when `--diarize` is set, creates `DiarizationPipeline(model_name=..., token=..., device=..., cache_dir=...)`, calls it for each input audio file, and applies `assign_word_speakers` before writing outputs.

| CLI flag | Diarization effect |
| --- | --- |
| `--diarize` | Enables pyannote diarization and speaker assignment. |
| `--hf_token TOKEN` | Passes a Hugging Face access token for gated pyannote models. Keep it secret. |
| `--diarize_model MODEL` | Selects diarization model; default is `pyannote/speaker-diarization-community-1`. |
| `--min_speakers N` | Minimum speaker count constraint. |
| `--max_speakers N` | Maximum speaker count constraint. |
| `--speaker_embeddings` | Includes speaker embeddings in JSON output only when `--diarize` is also active; otherwise it has no effect. |
| `--device cpu|cuda` | Device passed through to WhisperX processing, including diarization model placement. |
| `--model_dir DIR` | Also used as the diarization `cache_dir` in the CLI flow. |

The CLI does not expose Python API `num_speakers`; use `--min_speakers N --max_speakers N` for an exact CLI count.
