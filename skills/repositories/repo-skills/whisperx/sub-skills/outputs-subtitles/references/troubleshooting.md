# Troubleshooting output and subtitle rendering

Use this guide after validating that the transcript result came from the intended upstream workflow. If the problem is missing ASR text, missing alignment, or missing speaker assignment, route to the relevant upstream sub-skill before debugging writers.

## Quick checks

```bash
python scripts/validate_transcript_json.py transcript.json
python scripts/render_sample_outputs.py --transcript-json transcript.json --formats srt,vtt,json
```

Add `--require-word-timestamps` to the validator when `highlight_words=True` must work.

## Common failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| JSON file fails to load | Malformed JSON, trailing comma, wrong encoding, or a top-level list instead of object. | Re-save as UTF-8 JSON object. The top level should contain `language` and `segments`. Run the validator for exact field errors. |
| `KeyError: 'segments'`, `KeyError: 'language'`, or writer crashes immediately | Result dict is not writer-ready. Aligned results may omit `language` until the CLI write step adds it. | Add top-level `language` and `segments`; validate before calling `get_writer`. |
| `AssertionError: non-negative timestamp expected` | A segment or word timestamp is negative. | Repair timestamps before writing. Writers round to milliseconds but do not sanitize negative values. |
| Empty SRT/VTT/TXT output | `segments` is empty, or custom filtering removed all text. | Confirm upstream transcript content. Empty segments are structurally valid but produce empty files. |
| `highlight_words=True` produces no underlines | No aligned word `start`/`end` pairs are present, or subtitle writing used the segment-only branch. | Run validation with `--require-word-timestamps`; if timings are missing, route to `alignment-timestamps` or render plain subtitles without highlighting. |
| Highlighting crashes on a word | A word has `start` without `end`, or `end` without `start`. | Repair the word timing pair or remove both fields for that word. The validator flags one-sided timing pairs as errors. |
| Missing word timings but SRT/VTT still render | WhisperX can fall back to segment-level cue start/end when a cue has no timed words. | Treat this as readable subtitle fallback only, not word-level alignment evidence. Use `--require-word-timestamps` when timing accuracy is required. |
| Later segments crash in SRT/VTT word mode | The first segment has `words`, so the writer expects every segment to have `words`. | Normalize the result so all segments have `words`, or remove `words` from all segments for segment-only subtitles. |
| `max_line_count` seems ignored | `max_line_width` is `None`. WhisperX preserves segments when no width is set. | Set both `max_line_width` and `max_line_count`, for example width `42` and count `2`. |
| Lines are too wide for Japanese or Chinese | Standard `SubtitlesWriter` only removes spaces for `ja`/`zh`; it does not automatically lower width for all complex scripts. | Set explicit `max_line_width`, or use `SubtitlesProcessor` for complex-script-aware line-length defaults. |
| Highlighted Japanese/Chinese cues contain spaces | Highlight mode joins words with spaces while building underlined cues. | Avoid highlight mode for strict no-space display, or post-process highlighted VTT/SRT text. |
| Speaker labels appear in TXT/SRT/VTT but not TSV | Built-in TSV has columns `start`, `end`, `text` only. | Use JSON for structured speaker data, or create a custom TSV from JSON. |
| Speaker prefix is missing in subtitles | Writers look for segment-level `speaker` for visible prefixes. | If speaker labels exist only on words, propagate the chosen segment speaker to `segment["speaker"]` before writing. |
| Audacity does not open `.aud` as a project | WhisperX `.aud` is a tab-separated Audacity label text file, not an Audacity project. | In Audacity, import it as labels. Timestamps are seconds, with no header. Rename to `.txt` only if your workflow expects label text extension. |
| Subtitle parser rejects a cue containing `-->` | Segment-only subtitle path replaces `-->` with `->`; custom word-mode text may still need sanitization. | Avoid literal subtitle arrows in text or sanitize before writing. |
| SRT/VTT timestamps look different | SRT uses comma milliseconds and always includes hours; VTT uses dot milliseconds and may omit zero hours in the standard writer. | Choose the target format intentionally. For custom formatting, use the right helper: `whisperx.utils.format_timestamp` or `whisperx.SubtitlesProcessor.format_timestamp`. |

## Timestamp formatting checklist

- Inputs are seconds as Python numbers.
- Values must be non-negative.
- Values are rounded to the nearest millisecond.
- SRT cues use `HH:MM:SS,mmm`.
- VTT cues use dot milliseconds; the standard VTT writer omits the hours field below one hour.
- Audacity labels use decimal seconds, not milliseconds.
- TSV uses integer milliseconds.

## Choosing fallback versus repair

Segment-level fallback is acceptable for quick readable subtitles when word timestamps are unavailable. It is not acceptable when the task requires word highlighting, word-level timing accuracy, karaoke-style VTT, or validation of alignment quality. In those cases, repair the result through alignment or reject it with `scripts/validate_transcript_json.py --require-word-timestamps`.
