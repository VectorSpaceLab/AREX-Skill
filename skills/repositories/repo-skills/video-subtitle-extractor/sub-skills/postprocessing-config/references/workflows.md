# Post-processing Workflows

## From raw OCR to SRT

VSE stores raw OCR rows with frame number, coordinates, and text. It then:

1. Concatenates text with the same frame number.
2. Groups consecutive similar lines using Levenshtein ratio and
   `thresholdTextSimilarity`.
3. Chooses the longest text from each similar group.
4. Converts frame ranges to SRT timestamps using video FPS.
5. Uses VideoSubFinder timestamps when the VSF route was active.
6. Optionally applies `reformat.execute` for typo replacement and word
   segmentation.
7. Optionally writes TXT output from SRT text lines.

## Typo replacement

The typo map is JSON mapping regex patterns to replacement strings. A blank
replacement removes matched text. Always lint regex patterns before handing the
file to VSE:

```bash
python sub-skills/postprocessing-config/scripts/typo_map_lint.py --typo-map typoMap.json
```

## Safe smoke test

To test replacements without modifying a real subtitle file:

```bash
python sub-skills/postprocessing-config/scripts/reformat_smoke.py \
  --typo-map typoMap.json --sample-text "Iife isgood"
```

This helper applies regex replacements and reports a sample result. It is not a
full substitute for VSE's wordsegment/pysrt-based `reformat.execute`, but it
catches broken JSON/regex rules before a real run.

## Empty timestamps

When VideoSubFinder produces timestamps but OCR text is missing, `deleteEmptyTimeStamp`
controls whether empty intervals are preserved. Preserve them when timing is
valuable for manual correction; delete them for clean final subtitle files.
