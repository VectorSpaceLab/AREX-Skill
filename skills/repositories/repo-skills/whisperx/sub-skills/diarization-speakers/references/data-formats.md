# Diarization data formats

WhisperX speaker assignment combines a transcript result dictionary with diarization intervals. This reference describes the minimum shapes needed by `assign_word_speakers` and the bundled CSV helper.

## Transcript JSON before speaker assignment

The assignment function expects a dictionary with a top-level `segments` list. Segment and word timing values are seconds.

```json
{
  "language": "en",
  "segments": [
    {
      "start": 0.0,
      "end": 1.2,
      "text": "Hello there.",
      "words": [
        {"word": "Hello", "start": 0.05, "end": 0.45},
        {"word": "there.", "start": 0.50, "end": 1.05}
      ]
    }
  ]
}
```

Notes:

- Segment-level `start` and `end` default to `0.0` inside the assignment function if missing, but missing times usually indicate an upstream ASR/alignment problem.
- Word records without `start` are skipped for word-level speaker labels.
- A word with `start` but no `end` is treated as zero-duration at `start`; it usually needs `fill_nearest=True` to receive a label.
- Generating ASR or alignment output belongs to `asr-python-api` and `alignment-timestamps`.

## Diarization DataFrame

`DiarizationPipeline` returns a `pandas.DataFrame` containing at least these columns:

| Column | Type | Meaning |
| --- | --- | --- |
| `segment` | pyannote segment object | Original pyannote segment object. |
| `label` | object/string | Pyannote track label. |
| `speaker` | string | Speaker id, commonly `SPEAKER_00`, `SPEAKER_01`, ... |
| `start` | float seconds | Speaker interval start. |
| `end` | float seconds | Speaker interval end. |

`assign_word_speakers` only requires `start`, `end`, and `speaker`. Extra columns are ignored by assignment.

## Diarization CSV for the bundled helper

The bundled helper accepts CSV with exactly these required columns; extra columns are ignored.

```csv
start,end,speaker
0.00,1.20,SPEAKER_00
1.20,2.40,SPEAKER_01
2.40,3.10,SPEAKER_00
```

Validation rules enforced by the helper:

- Header must include `start`, `end`, and `speaker`.
- `start` and `end` must parse as finite numbers.
- Times must be non-negative seconds.
- `end` must be greater than `start` for every diarization interval.
- `speaker` must be non-empty after trimming whitespace.
- Empty CSV data is rejected by the helper so the user sees a clear error instead of silently producing no labels.

## Transcript JSON after assignment

After successful assignment, segments and words with matching intervals receive `speaker` fields.

```json
{
  "language": "en",
  "segments": [
    {
      "start": 0.0,
      "end": 1.2,
      "text": "Hello there.",
      "speaker": "SPEAKER_00",
      "words": [
        {"word": "Hello", "start": 0.05, "end": 0.45, "speaker": "SPEAKER_00"},
        {"word": "there.", "start": 0.50, "end": 1.05, "speaker": "SPEAKER_00"}
      ]
    }
  ]
}
```

When `speaker_embeddings` are supplied to `assign_word_speakers`, the result also receives a top-level field:

```json
{
  "speaker_embeddings": {
    "SPEAKER_00": [0.012, -0.034],
    "SPEAKER_01": [0.045, 0.006]
  }
}
```

The bundled CSV helper does not create embeddings.

## Overlap and nearest-speaker rules

For each transcript segment or word, WhisperX queries diarization intervals that overlap the item's `[start, end]` interval.

- If one speaker overlaps, that speaker is assigned.
- If multiple speakers overlap, WhisperX sums overlap duration by speaker and assigns the speaker with the largest total overlap.
- If no speaker overlaps and `fill_nearest=False`, no speaker field is added for that item.
- If no speaker overlaps and `fill_nearest=True`, WhisperX assigns the speaker whose diarization interval midpoint is nearest to the transcript item midpoint.

Use `fill_nearest=True` for timestamp drift, sparse word timings, or zero-duration word records where a nearby speaker is acceptable. Do not use it to disguise an empty or wrong diarization timebase.

## Empty or partially timed inputs

| Input condition | Assignment outcome | Action |
| --- | --- | --- |
| No transcript segments | Transcript is returned unchanged. | Route upstream to ASR/alignment. |
| Empty diarization DataFrame | Transcript is returned unchanged. | Diagnose model/token/audio or reject empty CSV in the helper. |
| Segment overlaps diarization but words lack starts | Segment may get `speaker`; words without starts stay unlabeled. | Route word-timestamp repair to `alignment-timestamps`. |
| Diarization times use milliseconds but transcript uses seconds | Overlaps fail or labels look wrong. | Convert both sources to seconds before assignment. |
