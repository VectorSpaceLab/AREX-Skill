# Troubleshooting

## Missing keys

**Symptom:** The validator reports missing `instruction`, `input`, or `output`.

**Likely cause:** The file is not Alpaca-shaped, or a conversion step dropped columns.

**Fix:** Restore the three required keys on every row. If the source is JSONL from another pipeline, normalize each record into the released Alpaca schema before training.

## Empty or invalid JSON

**Symptom:** The validator cannot parse the file, or it sees an empty dataset.

**Likely cause:** The file is truncated, not JSON/JSONL, or contains non-object rows.

**Fix:** Re-export the file, then rerun the validator in `--preview` mode before any training step.

## JSON vs. JSONL confusion

**Symptom:** The file parses in one mode but not the other.

**Likely cause:** A JSON array was saved with one object per line, or JSONL was wrapped in brackets.

**Fix:** Reformat the file into one of the two supported shapes and validate again.

## Prompt-format mismatch

**Symptom:** A preview shows the wrong Alpaca template, or a downstream training example looks too short/too long.

**Likely cause:** The row used the wrong branch for `input` handling.

**Fix:** Use the paired-input template only when `input` is non-empty. Use the no-input template when `input` is empty.

## Tokenizer pad/EOS assumptions

**Symptom:** Loss masking, padding, or decoded text looks odd.

**Likely cause:** The tokenizer lacks a pad token or EOS token, or a custom tokenizer behaves differently from the source script.

**Fix:** Mirror `train.py`: add missing special tokens, use right padding, and append the EOS token to each target string.

## Label masking confusion

**Symptom:** Training loss appears to include the prompt text.

**Likely cause:** The source prefix was not masked with `IGNORE_INDEX = -100`.

**Fix:** Confirm that the label tensor masks exactly the prompt tokens and leaves only the response tokens trainable.

## Blank outputs

**Symptom:** The validator warns about empty outputs.

**Likely cause:** The source release contains a small number of blank or near-blank targets, or a conversion step collapsed whitespace.

**Fix:** Decide whether those rows are acceptable for your workflow. Use `--require-nonempty-output` when you need a stricter corpus.

## License or intended-use concerns

**Symptom:** You need to know whether a derivative corpus can be shared, trained on, or used commercially.

**Likely cause:** Alpaca has mixed public statements across the repo and restricted-use language in the dedicated data/weight license files.

**Fix:** Read [intended use and licenses](intended-use-and-licenses.md). If the use is non-research, commercial, or redistribution-heavy, stop and get a policy/legal decision before proceeding.
