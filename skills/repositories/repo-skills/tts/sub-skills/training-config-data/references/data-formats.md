# Dataset Formatting and Sample Schemas

A TTS dataset needs audio clips plus text transcripts. The dataloader expects formatter output as dictionaries with normalized keys; train/eval splits are then produced by `load_tts_samples()`.

## Canonical formatter output

A formatter returns a list like:

```python
[
    {
        "text": "This is my sentence.",
        "audio_file": "data/my_dataset/wavs/audio1.wav",
        "speaker_name": "speaker_or_dataset_id",
        "root_path": "data/my_dataset"
    }
]
```

`load_tts_samples()` adds:

| Added key | Meaning |
| --- | --- |
| `language` | Dataset language from `BaseDatasetConfig.language`. |
| `audio_unique_name` | Stable key formed as `dataset_name#relative/audio/path` for embedding/d-vector maps and multi-dataset bookkeeping. |
| `alignment_file` | Optional attention-mask path when `meta_file_attn_mask` is configured. |

## LJSpeech-style layout

Use this for single-speaker custom datasets when possible:

```text
my_dataset/
  metadata.csv
  wavs/
    audio1.wav
    audio2.wav
```

Metadata rows are pipe-delimited:

```text
audio1|Raw transcription.|Normalized spoken transcription.
audio2|1469 and 1470|fourteen sixty-nine and fourteen seventy
```

The built-in `ljspeech` formatter reads column 1 as the basename, looks for `wavs/<basename>.wav`, and uses the normalized third column as `text`. If no separate normalized transcript exists, duplicate the transcript into the third column.

Minimum config:

```json
{
  "formatter": "ljspeech",
  "dataset_name": "my_ljspeech_style_data",
  "path": "data/my_dataset",
  "meta_file_train": "metadata.csv",
  "language": "en-us"
}
```

## Common Voice layout

The built-in `common_voice` formatter expects a tab-separated metadata file with a header beginning with `client_id`. It uses:

| Metadata column | Formatter use |
| --- | --- |
| `client_id` | Converted to speaker name `MCV_<client_id>`. |
| `path` | Audio filename under `clips/`; `.mp3` suffix is converted to `.wav`. |
| `sentence` | Training text. |

Expected layout after converting audio to wav:

```text
common_voice_subset/
  train.tsv
  clips/
    common_voice_x.wav
```

Use `ignored_speakers` to exclude client ids when needed.

## Coqui tabular layout

The `coqui` formatter expects a pipe-separated file with headers that include at least `audio_file` and `text`. Optional columns include `speaker_name` and `emotion_name`.

```text
audio_file|text|speaker_name
wavs/a.wav|Hello world.|speaker_a
```

Audio paths are interpreted relative to the dataset root.

## Custom formatter contract

If the dataset is not compatible with a built-in formatter, write a small Python formatter callable in the user's project code and pass it to `load_tts_samples()` from a training script. The callable shape is:

```python
def formatter(root_path, manifest_file, ignored_speakers=None, **kwargs):
    items = []
    # parse manifest_file and append dicts with text/audio_file/speaker_name/root_path
    return items
```

Keep these rules:

- Return absolute or user-working-directory-relative audio paths that exist.
- Always include `text`, `audio_file`, `speaker_name`, and `root_path` for TTS samples.
- For single-speaker datasets, use a stable dataset or speaker name.
- For multi-speaker datasets, use stable speaker ids and keep at least enough samples per speaker for eval splitting.
- If using multiple languages, set `language` in each dataset config and plan tokenizer/phonemizer behavior explicitly.

## Eval split behavior

`load_tts_samples(datasets, eval_split=True, eval_split_size=0.01, eval_split_max_size=None)` loads each configured dataset, then either:

- reads `meta_file_val` when provided, or
- derives an eval subset from train metadata.

For multi-speaker datasets, eval splitting preserves at least one sample per speaker when possible. Very tiny datasets can fail with an assertion that no eval sample can be created; increase `eval_split_size`, provide `meta_file_val`, or validate with `--no-eval-split` in `scripts/validate_tts_config.py` when only checking paths.

## Data quality checklist

Before training, check:

- Clips are lossless wav when possible; avoid compression artifacts.
- Transcript text matches the spoken audio and has no broken/wrong rows.
- Clip/text lengths are balanced; remove very long outliers and suspicious short-text/long-audio pairs.
- Background noise is low and recording tone/pitch is consistent for the target voice.
- The dataset covers target graphemes/phonemes, especially exceptional sounds.
- Sample rate is intentional, commonly around 16 kHz to 22.05 kHz for many TTS experiments unless the model/checkpoint expects otherwise.

Use `scripts/find_unique_symbols.py --mode chars` to inspect grapheme coverage. Use phoneme mode only when phonemizer dependencies are available.

## Multi-speaker and d-vector preparation

Multi-speaker TTS can use either learned speaker embeddings or precomputed d-vectors. If using d-vectors:

1. Validate the dataset and speaker ids first.
2. Use `audio_unique_name` keys consistently; they are based on `dataset_name` plus the relative audio path.
3. Use `scripts/compute_speaker_embeddings.py` in dry-run mode before computing embeddings.
4. Store generated speaker maps outside the skill tree and reference them from the user's training config.

Speaker-embedding computation is not inference and not full model training, but it can still be slow and may require an encoder checkpoint, CUDA, and disk space.

