# Transcript result data formats

WhisperX writers consume a Python dictionary shaped like the package's transcription/alignment results. The safest interchange form is UTF-8 JSON with a top-level `language` string and a `segments` list.

## Minimal writer-ready result

```json
{
  "language": "en",
  "segments": [
    {
      "start": 0.0,
      "end": 1.4,
      "text": "Hello world.",
      "speaker": "SPEAKER_00",
      "words": [
        {"word": "Hello", "start": 0.0, "end": 0.5, "score": 0.99},
        {"word": "world.", "start": 0.6, "end": 1.2, "score": 0.98}
      ]
    }
  ]
}
```

`words` and `speaker` are optional for basic text/TSV/JSON output. `language` is required for word-mode SRT/VTT writing because the subtitle writer checks whether the language should be joined without spaces.

## Schema fields distilled from WhisperX types

### Top-level result

| Field | Required for writers | Type | Notes |
| --- | --- | --- | --- |
| `segments` | yes | list of segment objects | Empty lists are valid but produce empty text/subtitle outputs. |
| `language` | yes for writer-ready JSON | string language code | CLI writing sets this before output. Add it when saving aligned results directly. |
| `word_segments` | no | list of word objects | Present in aligned results; not used by the standard writers. |
| other fields | no | any JSON-compatible value | JSON writer preserves them; other writers ignore them. |

### Segment object

| Field | Required | Type | Used by |
| --- | --- | --- | --- |
| `start` | yes | non-negative number, seconds | SRT/VTT fallback, TSV, Audacity labels. |
| `end` | yes | non-negative number, seconds, `>= start` | SRT/VTT fallback, TSV, Audacity labels. |
| `text` | yes | string | All text-bearing formats. |
| `words` | no | list of word objects | Word-mode SRT/VTT line splitting and highlighting. |
| `speaker` | no | string | TXT/SRT/VTT/Audacity speaker prefixes. |
| `chars` | no | list of char timing objects or null | Preserved only by JSON writer. |
| `avg_logprob` | no | number | Preserved only by JSON writer. |

### Word object

| Field | Required if `words` is present | Type | Used by |
| --- | --- | --- | --- |
| `word` | yes | string | Subtitle text construction. |
| `start` | recommended with `end` | non-negative number, seconds | Word-mode cue timing and highlighting. |
| `end` | recommended with `start` | non-negative number, seconds, `>= start` | Word-mode cue timing and highlighting. |
| `score` | no | number | Preserved by JSON; not used by standard writers. |
| `speaker` | no | string | Preserved by JSON; standard subtitle writer uses segment-level speaker for visible prefixes. |

A word may lack both `start` and `end` when alignment used an ignore/fallback path. Standard SRT/VTT can still render using segment-level fallback when no timed words are available in a cue, but `highlight_words=True` needs word timing pairs to underline words accurately.

## Segment-only versus word-mode subtitle results

The standard SRT/VTT writer chooses its rendering branch by checking whether the **first segment** has a `words` field.

- If the first segment has `words`, keep `words` present on every segment to avoid writer errors.
- If the first segment has no `words`, later `words` fields are ignored by the subtitle writer.
- For predictable post-processing, either provide `words` for all segments or omit `words` from all segments.

## Speaker fields

Speaker labels are not part of the strict `TypedDict` segment definitions but are added by WhisperX speaker assignment workflows. Writers handle them as follows:

- `txt`: `[SPEAKER_ID]: text`
- `srt`/`vtt`: `[SPEAKER_ID]: text`
- `aud`: `[[SPEAKER_ID]]text`
- `json`: preserves raw fields
- `tsv`: no automatic separate speaker field

If you need speaker-labeled TSV, create it as a custom post-processing step from JSON rather than expecting the built-in TSV writer to add a speaker column.

## Validation helper

Use the bundled validator before rendering user-supplied JSON:

```bash
python scripts/validate_transcript_json.py transcript.json
```

Useful stricter modes:

```bash
# Fail if any segment lacks words.
python scripts/validate_transcript_json.py transcript.json --require-words

# Fail unless every word has start/end timing pairs suitable for highlighting.
python scripts/validate_transcript_json.py transcript.json --require-word-timestamps
```

The validator reports malformed JSON, missing required fields, non-finite or negative timestamps, `end < start`, mixed word-mode hazards, and word-timing gaps that affect highlighting.
