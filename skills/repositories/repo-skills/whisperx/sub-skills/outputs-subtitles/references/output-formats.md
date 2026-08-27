# Output formats and writer API

WhisperX output writing is pure post-processing: it consumes a transcript result dictionary and writes files. The writer functions do not run ASR, alignment, diarization, audio decoding, or model downloads.

## Public writer entry point

```python
from whisperx.utils import get_writer

writer = get_writer(output_format="srt", output_dir="outputs")
writer(result, "audio.wav", {
    "highlight_words": False,
    "max_line_width": None,
    "max_line_count": None,
})
```

Verified API surface for this version:

| Object | Call shape | Use |
| --- | --- | --- |
| `whisperx.utils.get_writer` | `(output_format: str, output_dir: str) -> Callable[[dict, str, dict], None]` | Selects and instantiates a writer. |
| `WriteTXT` | writer class, extension `txt` | Plain transcript text, one segment per line. |
| `WriteSRT` | writer class, extension `srt` | SubRip subtitles with cue indexes and comma millisecond separator. |
| `WriteVTT` | writer class, extension `vtt` | WebVTT subtitles with `WEBVTT` header and dot millisecond separator. |
| `WriteTSV` | writer class, extension `tsv` | Tab-separated `start`, `end`, `text`, with times in integer milliseconds. |
| `WriteJSON` | writer class, extension `json` | Raw result JSON via `json.dump(..., ensure_ascii=False)`. |
| `WriteAudacity` | writer class, extension `aud` | Audacity label text using seconds, tab separators, and no header. |

`get_writer("all", output_dir)` writes the core `txt`, `vtt`, `srt`, `tsv`, and `json` files. It does **not** include the optional Audacity writer; request `aud` explicitly when Audacity labels are needed.

## Output file naming

All writers derive the output filename from the basename of the `audio_path` argument and the writer extension. The audio file is not opened by the writer; the path is only used to choose the output basename.

Example: passing `audio_path="meeting.wav"` with `output_format="srt"` writes `meeting.srt` inside `output_dir`.

## Writer options

Every writer call should receive the same options dictionary, even for formats that ignore some fields:

| Option | Type | Applies to | Behavior |
| --- | --- | --- | --- |
| `highlight_words` | `bool` | SRT/VTT word-mode subtitles | Underlines each timed word with `<u>...</u>` across separate cues. Requires word timestamps; otherwise WhisperX falls back to non-highlighted text. |
| `max_line_width` | `int | None` | SRT/VTT word-mode subtitles | Maximum characters before a line break. `None` means effectively unbounded writer width. |
| `max_line_count` | `int | None` | SRT/VTT word-mode subtitles | Maximum lines per cue, but only has an effect when `max_line_width` is also set. |

The CLI emits a warning when `max_line_count` is set without `max_line_width`; do the same in custom post-processors because the writer preserves segments in that case.

## Format-specific behavior

| Format | Contents | Timing style | Speaker behavior | Notes |
| --- | --- | --- | --- | --- |
| `txt` | One stripped segment text per line | None | Prefixes `[SPEAKER_ID]: ` when `segment["speaker"]` exists. | Good for human-readable plain text, not structured timing. |
| `json` | Full result dictionary | JSON numbers as supplied | Preserves any `speaker`, `words`, `chars`, `word_segments`, and embeddings fields present. | Use for downstream processing or round-tripping. |
| `tsv` | Header `start\tend\ttext`, then segment rows | Integer milliseconds | Does not add a separate speaker column; speaker labels appear only if already in `text`. | Replaces tabs in text with spaces. |
| `srt` | Numbered cues | `HH:MM:SS,mmm` | Prefixes `[SPEAKER_ID]: ` in each cue when segment speaker exists. | Replaces literal `-->` with `->` in segment-only subtitle text. |
| `vtt` | `WEBVTT` header plus cues | `MM:SS.mmm` below 1 hour, `HH:MM:SS.mmm` at/above 1 hour | Prefixes `[SPEAKER_ID]: ` in each cue when segment speaker exists. | Uses dot milliseconds. |
| `aud` | Audacity label rows | Seconds as decimal values | Prefixes `[[SPEAKER_ID]]` inside the label text. | The `.aud` extension is a WhisperX convention for label text; it is not an Audacity project file. |

## Timestamp helpers

`whisperx.utils.format_timestamp(seconds, always_include_hours=False, decimal_marker=".")` rounds seconds to milliseconds and asserts that the timestamp is non-negative.

Writer defaults:

- SRT: `always_include_hours=True`, `decimal_marker=","`, e.g. `00:00:01,230`.
- VTT: `always_include_hours=False`, `decimal_marker="."`, e.g. `00:01.230` below one hour.

`whisperx.SubtitlesProcessor.format_timestamp(seconds, is_vtt=False)` is a separate helper used by `SubtitlesProcessor`; it always includes the hours field and uses `,` for SRT-style output or `.` for VTT-style output.

## Direct writer recipe

```python
from pathlib import Path
from whisperx.utils import get_writer

result = {
    "language": "en",
    "segments": [
        {
            "start": 0.0,
            "end": 1.4,
            "text": "Hello world.",
            "speaker": "SPEAKER_00",
            "words": [
                {"word": "Hello", "start": 0.0, "end": 0.5, "score": 0.99},
                {"word": "world.", "start": 0.6, "end": 1.2, "score": 0.98},
            ],
        }
    ],
}

out_dir = Path("outputs")
out_dir.mkdir(parents=True, exist_ok=True)
writer = get_writer("vtt", str(out_dir))
writer(result, "sample.wav", {
    "highlight_words": True,
    "max_line_width": 42,
    "max_line_count": 2,
})
```

Use `scripts/render_sample_outputs.py` for a ready-to-run safe version of this pattern.
