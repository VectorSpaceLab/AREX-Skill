# Evaluation troubleshooting

## Batch score has missing or unexpected pairs

**Symptom:** A batch score ignores some files, or the matched-pair count is lower than expected.

**Cause:** SketchCode batch evaluation iterates over predicted filenames containing `.gui`, sorts them, and only scores a predicted file when the original folder contains a file with the exact same filename. Extra predicted files without matching originals are skipped. Extra originals without predictions are ignored.

**Fix:** Make filenames identical across the two folders before scoring. Use the bundled helper with `--show-skipped` to list predicted files that did not have a matching original:

```bash
python scripts/evaluate_tiny_gui_bleu.py \
  --original-guis-dir original_guis \
  --predicted-guis-dir predicted_guis \
  --show-skipped
```

If zero pairs match, do not interpret the BLEU value; fix the folder layout first.

## Predicted `.gui` extension filtering is surprising

**Symptom:** A predicted file is ignored, or a backup file is accidentally included.

**Cause:** The source batch loader keeps predicted entry names where the case-sensitive substring `.gui` appears. This is close to extension filtering but not exactly a strict suffix check: `sample.gui` is included, `.GUI` is not included, and names such as `sample.gui.bak` can be included by strict source-compatible logic.

**Fix:** Keep the predicted folder clean. Use lowercase `.gui` filenames for intended predictions and move backups, logs, or intermediate files out of the predicted folder before scoring.

## BLEU is near zero even though files look similar

**Likely causes:**

- Prediction boundary mismatch: SketchCode strips the first and last predicted tokens before BLEU. If the prediction lacks start/end wrapper tokens, two real GUI DSL tokens are removed.
- Tokenization mismatch: whitespace is collapsed, then commas are converted with `replace(',', ' ,')`, then text is split on whitespace. Compact comma usage such as `button,btn-red` can produce different tokens than `button, btn-red`.
- Order sensitivity: BLEU rewards overlapping token n-grams, so reordered but semantically similar GUI DSL can score poorly.
- Very short sequences: default BLEU-4 can be harsh when there are not enough higher-order n-grams.

**Fix:** Inspect normalized tokens before interpreting the score:

```bash
python scripts/evaluate_tiny_gui_bleu.py \
  --original-gui-file expected.gui \
  --predicted-gui-file predicted.gui \
  --show-tokens
```

For strict SketchCode compatibility, ensure generated predictions include boundary tokens before the first real DSL token and after the last real DSL token. For diagnostic-only scoring, you may compare normalized tokens directly, but record that it is not the original SketchCode BLEU contract.

## NLTK import or version issues

**Symptom:** Evaluation fails with `ModuleNotFoundError: No module named 'nltk'`, cannot import `nltk.translate.bleu_score`, or emits version-dependent warnings.

**Cause:** SketchCode's original dependency set used an old NLTK release, while current environments may have a different NLTK or none at all.

**Fix:** For real BLEU scores, install a compatible NLTK in the active environment and rerun. For smoke checks, use the bundled helper without NLTK; it falls back to an exact-match score after SketchCode-style normalization and prediction trimming. Do not publish fallback scores as BLEU.

## Short sequence warnings

**Symptom:** NLTK warns that the hypothesis contains zero counts of 2-gram, 3-gram, or 4-gram overlaps, or the BLEU score is effectively zero for a tiny GUI.

**Cause:** Source behavior calls NLTK sentence/corpus BLEU with default settings and no smoothing. Default BLEU-4 is unstable on very short token sequences.

**Fix:** Prefer longer representative GUI fixtures when interpreting BLEU. If you use smoothing for diagnostics, label the result as smoothed and do not compare it directly with strict SketchCode scores.

## Button color or active-state results look wrong

**Symptom:** Predictions with different button colors score the same, or `btn-inactive` differences disappear.

**Cause:** `Evaluator.load_gui_doc` normalizes color/state tokens before BLEU:

- `btn-green` and `btn-red` become `btn-orange`.
- `btn-inactive` becomes `btn-active`.

This was intentional because predicted sketch images do not reliably preserve button color.

**Fix:** If the task cares about exact color or active/inactive state, BLEU from the SketchCode evaluator is not enough. Inspect normalized tokens and raw tokens separately, then add a task-specific assertion for color/state fidelity.

## Button normalization did not happen

**Symptom:** `btn-red` or `btn-green` was expected to normalize but still appears in tokens.

**Cause:** Normalization is token-exact and happens after the comma spacing step. If punctuation remains attached, for example `,btn-red`, it is not equal to `btn-red` and will not normalize.

**Fix:** Format `.gui` text with whitespace after commas, such as `button, btn-red`, before scoring. Use `--show-tokens` to verify the final token lists.
