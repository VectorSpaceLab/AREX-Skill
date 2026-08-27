# Post-processing API Reference

## `reformat.execute(path, lang='en')`

Reads an SRT file, applies typo replacement from VSE's typo map, optionally
segments English-like concatenated words with `wordsegment`, normalizes spacing
and punctuation, saves the SRT, and returns `True`/`False`.

Important behavior:

- Returns `False` if the SRT path cannot be opened or saved.
- Catches individual subtitle-line errors and continues when possible.
- Limits very long subtitle text before word segmentation.
- Applies typo replacements before and after segmentation.

## SRT/TXT generation surfaces

`SubtitleExtractor.generate_subtitle_file()` writes frame-derived SRT intervals.
`generate_subtitle_file_vsf()` combines VideoSubFinder timing with OCR text and
respects `deleteEmptyTimeStamp`. `srt2txt()` writes each subtitle text to a TXT
file when `generateTxt` is enabled.

## Coordinate and duplicate helpers

- `_concat_content_with_same_frameno()` merges OCR rows with identical frame ids.
- `_remove_duplicate_subtitle()` groups similar text using Levenshtein ratio.
- `_unite_coordinates()` normalizes similar OCR boxes with configured X/Y pixel
  tolerance.
