# Post-processing Troubleshooting

## Typo map breaks cleanup

Run `typo_map_lint.py`. If a pattern fails to compile, escape special regex
characters or replace it with a safer literal pattern.

## Valid subtitles are dropped

- Lower `dropScore` only after confirming OCR boxes are in the selected area.
- Increase `subtitleAreaDeviationRate` for subtitles slightly outside the drawn
  rectangle.
- Expand the selected subtitle area for multi-line subtitles.
- Check language mode; English filtering removes CJK characters.

## Too many duplicate or merged lines

Tune `thresholdTextSimilarity`: higher values split similar lines more often;
lower values merge more aggressively. For fast-moving subtitles, verify frame
sampling and VideoSubFinder timing before changing text similarity.

## Word segmentation damages text

Disable `wordSegmentation` for languages or OCR output where English word
segmentation is not appropriate. Keep typo replacements narrowly targeted.

## Need manual correction

Preserve empty timestamps and enable debug cache/loss outputs for diagnosis;
turn them off for final production runs to keep output clean.
