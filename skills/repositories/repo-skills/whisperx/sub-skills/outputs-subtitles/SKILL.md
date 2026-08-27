---
name: outputs-subtitles
description: "Use WhisperX output writers and subtitle post-processing without
  running ASR models."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 2-Clause
---

# WhisperX output and subtitle files

Use this sub-skill when you already have a WhisperX-style transcript result and need to validate it, write output files, or tune subtitle post-processing. It covers the `txt`, `json`, `tsv`, `srt`, `vtt`, and Audacity label writer surfaces, speaker prefixes, word highlighting, line width/count behavior, complex-script splitting, timestamp formatting, and safe synthetic rendering.

Do **not** use this sub-skill to create transcript results from audio or models. Route ASR/model loading to `asr-python-api`, forced word timestamps to `alignment-timestamps`, speaker assignment to `diarization-speakers`, and CLI command construction to `transcription-cli`.

## What to read

- [`references/output-formats.md`](references/output-formats.md): use for `get_writer`, writer classes, output extensions, writer options, timestamp styles, and speaker prefix behavior.
- [`references/subtitle-processing.md`](references/subtitle-processing.md): use for `SubtitlesWriter.iterate_result`, `SubtitlesProcessor`, word highlighting, line wrapping, language-without-spaces behavior, conjunction/comma splitting, and missing-word-timing fallback.
- [`references/data-formats.md`](references/data-formats.md): use before handing a result dict or JSON file to a writer; includes the minimal WhisperX result schema and writer-read fields.
- [`references/troubleshooting.md`](references/troubleshooting.md): use when output rendering fails, subtitle cues look wrong, word highlighting is absent, speaker labels are unexpected, Audacity labels do not import as expected, or timestamps appear in the wrong style.

## Bundled helpers

- [`scripts/validate_transcript_json.py`](scripts/validate_transcript_json.py): run this on a transcript JSON file before writing outputs; it checks the minimal WhisperX result shape and can require word timestamps for highlighting-ready subtitles.
- [`scripts/render_sample_outputs.py`](scripts/render_sample_outputs.py): render a tiny in-memory transcript or a provided transcript JSON through `whisperx.utils.get_writer`; it never calls ASR, alignment, diarization, model downloads, credentials, or audio decoding.

## Minimal workflow

1. Confirm the result object has top-level `language` and `segments` fields. See [`references/data-formats.md`](references/data-formats.md).
2. If reading JSON from disk, validate it first:
   ```bash
   python scripts/validate_transcript_json.py transcript.json
   ```
3. For subtitle formats, decide whether word-level behavior is required:
   - use aligned results with `words[].start`/`words[].end` for `highlight_words=True`;
   - use segment-only results when plain SRT/VTT cues are sufficient;
   - set `max_line_width` whenever `max_line_count` should matter.
4. Render via the WhisperX writer API or the bundled sample renderer. See [`references/output-formats.md`](references/output-formats.md).

## Safe examples

Render speaker-labeled SRT, VTT, and JSON from an in-memory sample without model execution:

```bash
python scripts/render_sample_outputs.py --formats srt,vtt,json --highlight-words
```

Diagnose missing word timestamps while still producing segment-level subtitle cues:

```bash
python scripts/render_sample_outputs.py --sample missing-word-timings --formats srt,vtt --highlight-words
```
