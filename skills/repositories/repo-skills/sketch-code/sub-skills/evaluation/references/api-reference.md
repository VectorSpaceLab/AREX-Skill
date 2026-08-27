# Evaluation API reference

This reference captures the source-evidenced behavior of SketchCode evaluation without requiring runtime access to the original scripts.

## CLI entry points and flags

| Interface | Required flags | Output behavior |
| --- | --- | --- |
| Single GUI evaluator | `--original_gui_filepath`, `--predicted_gui_filepath` | Prints `BLEU score for single GUI: <score>`. |
| Batch GUI evaluator | `--original_guis_filepath`, `--predicted_guis_filepath` | Prints `BLEU score for batch of GUIs: <score>`. |

The bundled helper uses hyphenated option names for portability, but its normalization and pairing behavior are aligned with the distilled `Evaluator` contract below.

## `Evaluator.load_gui_doc(gui_filepath)`

Purpose: read one `.gui` text file and return normalized tokens.

Distilled behavior:

```text
gui_text = read_file(gui_filepath)
gui_text = " ".join(gui_text.split())
gui_text = gui_text.replace(",", " ,")
tokens   = gui_text.split()
tokens   = ["btn-orange" if token in {"btn-green", "btn-red"} else token for token in tokens]
tokens   = ["btn-active" if token == "btn-inactive" else token for token in tokens]
return tokens
```

Important details:

- Whitespace normalization happens before comma spacing.
- Comma handling inserts a space before each comma. It does not explicitly insert a space after each comma; compact strings like `button,btn-red` can tokenize differently from `button, btn-red`.
- Button normalization is token-exact. `btn-red` normalizes, but comma-attached text such as `,btn-red` does not become `btn-orange` unless tokenization separated it first.
- `btn-green` and `btn-red` both normalize to `btn-orange` because predicted images do not carry reliable button color. `btn-inactive` normalizes to `btn-active`.

## `Evaluator.get_sentence_bleu(original_gui_filepath, generated_gui_filepath)`

Purpose: compute one sentence BLEU score.

Distilled behavior:

```text
original_gui  = load_gui_doc(original_gui_filepath)
generated_gui = load_gui_doc(generated_gui_filepath)
hypothesis    = generated_gui[1:-1]
references    = [original_gui]
return sentence_bleu(references, hypothesis)
```

Consequences:

- The original/reference token list is not trimmed.
- The predicted/generated token list loses its first and last tokens before scoring.
- This matches model-generated sequences that contain boundary tokens. For predictions without boundary tokens, strict scoring drops two real tokens.
- Source behavior uses NLTK's default `sentence_bleu` settings and no smoothing function.

## `Evaluator.load_guis_from_folder(original_guis_filepath, predicted_guis_filepath)`

Purpose: build reference and hypothesis corpora for batch scoring.

Distilled behavior:

```text
predicted_names = list_dir(predicted_guis_filepath)
predicted_guis  = [name for name in predicted_names if ".gui" appears in name]
sort(predicted_guis)

actuals   = []
predicted = []
for name in predicted_guis:
    predicted_file = predicted_guis_filepath / name
    original_file  = original_guis_filepath / name
    if original_file is a file:
        predicted_tokens = load_gui_doc(predicted_file)
        original_tokens  = load_gui_doc(original_file)
        predicted.append(predicted_tokens[1:-1])
        actuals.append([original_tokens])
return actuals, predicted
```

Consequences:

- Matching is by exact filename, not by folder order.
- Predicted entries are considered only when their name contains `.gui` case-sensitively.
- Predicted GUI names are sorted before processing.
- A predicted file without a matching original is skipped.
- An original file without a predicted counterpart is ignored.

## `Evaluator.get_corpus_bleu(original_guis_filepath, predicted_guis_filepath)`

Purpose: compute batch corpus BLEU.

Distilled behavior:

```text
actuals, predicted = load_guis_from_folder(original_guis_filepath, predicted_guis_filepath)
return corpus_bleu(actuals, predicted)
```

Always confirm `len(actuals) == len(predicted)` and that the count is nonzero before interpreting a batch BLEU value.

## Bundled helper mapping

`../scripts/evaluate_tiny_gui_bleu.py` implements the same core normalization, prediction trimming, and batch pairing rules in a self-contained form. Use it for:

- Tiny fixture smoke checks.
- Diagnosing tokenization and button normalization.
- Scoring ad hoc `.gui` files when NLTK is available.
- Exact-match fallback checks when NLTK is not installed.

For workflow examples, see [evaluation-workflow.md](evaluation-workflow.md). For failure modes, see [troubleshooting.md](troubleshooting.md).
