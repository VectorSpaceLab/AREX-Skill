# Evaluation workflow

Use this reference to compute and interpret SketchCode BLEU scores for `.gui` files. The behavior here is distilled from the SketchCode README evaluation commands, the single and batch evaluator entry points, and the `Evaluator` class.

## Fast self-contained checks

From this sub-skill directory, run the bundled helper:

```bash
python scripts/evaluate_tiny_gui_bleu.py --mode smoke --show-tokens
```

The smoke fixture deliberately uses different button colors in the original and prediction. SketchCode normalizes `btn-green` and `btn-red` to `btn-orange` before BLEU, so the fixture should show a normalized exact match even though the raw strings differ.

For your own single pair:

```bash
python scripts/evaluate_tiny_gui_bleu.py \
  --original-gui-file expected.gui \
  --predicted-gui-file predicted.gui \
  --show-tokens
```

For folders:

```bash
python scripts/evaluate_tiny_gui_bleu.py \
  --original-guis-dir original_guis \
  --predicted-guis-dir predicted_guis \
  --show-skipped
```

The helper uses NLTK BLEU when `nltk.translate.bleu_score` is importable. If NLTK is unavailable, it prints an exact-match fallback score so future agents can still verify normalization and start/end trimming on tiny fixtures. Treat fallback scores as a smoke check, not as a substitute for published BLEU.

## Original CLI flag contract

SketchCode's source-evidenced public evaluation interfaces are:

- Single GUI: `evaluate_single_gui.py` with `--original_gui_filepath` and `--predicted_gui_filepath`.
- Batch GUI folders: `evaluate_batch_guis.py` with `--original_guis_filepath` and `--predicted_guis_filepath`.

Use those flag names when maintaining a SketchCode-compatible CLI. Prefer the bundled helper above when you only need self-contained evaluation behavior and do not have an original source script available.

## What is scored

SketchCode scores tokenized GUI DSL text, not rendered HTML semantics.

1. Read each `.gui` file as text.
2. Collapse all whitespace runs to single spaces.
3. Insert a space before commas, then split on whitespace.
4. Normalize button color/state tokens:
   - `btn-green` and `btn-red` become `btn-orange`.
   - `btn-inactive` becomes `btn-active`.
5. For predictions only, remove the first and last tokens before scoring.
6. Use the original tokens as one reference and the trimmed predicted tokens as the hypothesis.

Step 5 assumes predicted GUI sequences include boundary tokens such as start/end markers. If your prediction does not include wrapper tokens, the first and last real DSL tokens will be dropped by strict SketchCode-compatible scoring.

## Single-file scoring

The single evaluator computes sentence BLEU over one pair:

```text
reference  = load_gui_doc(original_gui_filepath)
hypothesis = load_gui_doc(predicted_gui_filepath)[1:-1]
score      = sentence_bleu([reference], hypothesis)
```

Interpretation notes:

- `1.0` means a perfect normalized token match under the active NLTK BLEU implementation.
- Low scores can come from real DSL differences, tokenization differences, missing prediction boundary tokens, or very short sequences with no higher-order n-gram overlap.
- The source behavior does not apply BLEU smoothing.

## Batch folder scoring

The batch evaluator computes corpus BLEU over sorted predicted filenames:

1. List predicted folder entries.
2. Keep names containing the case-sensitive substring `.gui`.
3. Sort those predicted filenames lexicographically.
4. For each predicted filename, look for an original file with the exact same filename.
5. Score only pairs where the matching original file exists.
6. For each pair, append `[original_tokens]` to the reference corpus and `predicted_tokens[1:-1]` to the hypothesis corpus.
7. Compute `corpus_bleu(actuals, predicted)`.

Extra predicted files without matching originals are skipped, not renamed or matched by order. Extra original files without predicted counterparts are ignored. Always inspect the matched-pair count before trusting a batch score.

## When to use BLEU carefully

BLEU is a token-overlap metric. It does not verify whether GUI DSL compiles, whether rendered HTML looks correct, or whether two valid DSL variants are semantically equivalent. For conversion problems, combine BLEU with conversion-inference checks when the user's goal is usable generated HTML rather than only text similarity.
