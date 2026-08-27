# Subtitle post-processing behavior

WhisperX has two subtitle-related surfaces:

1. `whisperx.utils.SubtitlesWriter` and its `WriteSRT`/`WriteVTT` subclasses, used by `get_writer("srt"|"vtt", ...)`.
2. `whisperx.SubtitlesProcessor.SubtitlesProcessor`, a separate segment splitter that can produce SRT/VTT-style subtitle fragments using conjunction and comma heuristics.

Both surfaces are pure result post-processing. They do not transcribe audio or produce alignments.

## `SubtitlesWriter.iterate_result`

`WriteSRT` and `WriteVTT` call `SubtitlesWriter.iterate_result(result, options)` and then serialize each yielded cue. The options dictionary must contain:

```python
{
    "highlight_words": bool,
    "max_line_width": int | None,
    "max_line_count": int | None,
}
```

### Word-mode path

If the first segment has a `words` field, the writer enters word mode and expects every segment it iterates to have `words`.

Word mode uses word dictionaries to build subtitle lines:

- `max_line_width=None` is treated as a very large line width.
- `preserve_segments=True` when `max_line_count is None` or `max_line_width is None`.
- A new cue can be forced by segment boundaries when preserving segments, by long pauses over roughly 3 seconds when not preserving segments, or by the configured line-count limit.
- Cue start/end times are taken from the minimum timed word start and maximum timed word end in the cue.
- If no word in a cue has start/end timing, cue start/end fall back to the segment-level `start`/`end` values captured for the words.

For languages in `whisperx.utils.LANGUAGES_WITHOUT_SPACES` (`ja`, `zh`), non-highlighted word-mode cue text is concatenated without spaces. Other languages join words with spaces.

### Segment-only path

If the first segment does not have `words`, SRT/VTT writing uses segment-level timestamps and `segment["text"]` directly. In this path:

- word highlighting is not applied;
- line width/count options do not split text;
- literal `-->` in segment text is replaced with `->` to avoid confusing subtitle parsers;
- `segment["speaker"]`, when present, is rendered as `[SPEAKER_ID]: text`.

### Word highlighting

When `highlight_words=True` and at least one word in a subtitle has timing, the writer emits timed cues with the current word underlined as `<u>word</u>`. It also emits plain full-subtitle cues to cover gaps between timed words.

Important limitations:

- Highlighting needs aligned word `start` and `end` pairs. If word timings are absent, the subtitle still renders but is not word-highlighted.
- A word with `start` but no `end` can fail during highlighting; validate or repair such records first.
- In highlighted cues, words are joined with spaces even for `ja`/`zh`; if this is unacceptable, post-process the VTT/SRT text or avoid highlighted mode for those languages.

### Speaker prefixes

In word mode, the speaker prefix is copied from the segment associated with the first word in a cue. In segment-only mode, it is copied from the segment. The prefix is `[SPEAKER_ID]: ` for SRT/VTT.

If diarization assigns speaker labels only at word level but not segment level, normalize the result before writing if visible labels are required in subtitles.

## `SubtitlesProcessor`

Verified constructor:

```python
from whisperx.SubtitlesProcessor import SubtitlesProcessor

processor = SubtitlesProcessor(
    segments,
    lang="en",
    max_line_length=45,
    min_char_length_splitter=30,
    is_vtt=False,
)
```

`SubtitlesProcessor` is useful when you want more sentence-like fragment splitting than `SubtitlesWriter` gives. It accepts a list of segment dictionaries and can use either word dictionaries or text-split words.

### Complex-script length defaults

For complex-script languages, `SubtitlesProcessor` tightens line-length settings to `max_line_length=30` and `min_char_length_splitter=20`. The built-in complex-script list includes:

`th`, `lo`, `my`, `km`, `am`, `ko`, `ja`, `zh`, `ti`, `ta`, `te`, `kn`, `ml`, `hi`, `ne`, `mr`, `ar`, `fa`, `ur`, `ka`.

This is broader than `LANGUAGES_WITHOUT_SPACES`, which only controls no-space joining for `ja` and `zh` in `SubtitlesWriter`.

### Split-point heuristics

`SubtitlesProcessor.determine_advanced_split_points(...)` considers:

- accumulated character count relative to `max_line_length`;
- whether there are enough characters before and after a possible split (`min_char_length_splitter`);
- language-specific comma punctuation from `get_comma(lang)`;
- language-specific conjunction words from `get_conjunctions(lang)`.

Comma behavior:

| Language | Comma character |
| --- | --- |
| `ja` | `、` |
| `zh` | `，` |
| `fa` | `،` |
| `ur` | `،` |
| all other languages | `,` |

Conjunction lists are available for many common languages such as English, French, German, Spanish, Italian, Japanese, Chinese, Arabic, Hindi, Korean, and others. If a language is missing from the conjunction map, only comma and length splitting apply.

### Missing word timestamp estimates

When a word dictionary lacks `start` or `end`, `SubtitlesProcessor.estimate_timestamp_for_word(...)` mutates that word with an estimated interval. It uses nearby word boundaries when possible, the next segment start when available, or a simple character-length estimate as a final fallback.

Use this as a convenience for readable subtitle splitting, not as proof of forced-alignment accuracy. If accurate word timings matter, route to `alignment-timestamps` first.

### Save behavior

`SubtitlesProcessor.save(filename="subtitles.srt", advanced_splitting=True)` writes a file and returns the number of subtitle fragments. With `is_vtt=True`, it adds a `WEBVTT` header and uses dot milliseconds. In this version, `save()` writes cues through the advanced-splitting branch; if you call `process_segments(advanced_splitting=False)`, write those returned segments yourself or use the standard `WriteSRT`/`WriteVTT` writers.

## Choosing a subtitle surface

| Need | Prefer |
| --- | --- |
| Match WhisperX CLI output files | `get_writer("srt"|"vtt", ...)` |
| Word-by-word underline highlighting | `get_writer` SRT/VTT with aligned `words[].start/end` |
| Segment-only subtitle fallback | `get_writer` SRT/VTT with no `words` field |
| Heuristic sentence/line splitting using conjunctions and commas | `SubtitlesProcessor` |
| Complex-script line length adjustment | `SubtitlesProcessor`, or manual writer options plus language-aware post-processing |
