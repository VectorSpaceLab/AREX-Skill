---
name: gsm8k_answer_tools
description: Extract GSM8K final answers, validate calculator annotations, and label candidate solutions by answer correctness.
---

# GSM8K Answer Tools

Use this skill when working with GSM8K-style math word problem examples or candidate solutions from the verifier pipeline. It provides deterministic answer extraction, numeric canonicalization, calculator annotation checks, and correctness labels.

Do not use this skill as a full verifier. It does not judge reasoning quality beyond final-answer matching and calculator annotation validity.

## Inputs

- JSONL rows with `question` and `answer`.
- Candidate solution strings that should contain a final `####` answer marker.
- Optional calculator annotations in the form `<<expression=result>>`.

## Outputs

- Canonical answer strings.
- Calculator validation records.
- Candidate label records with extracted answer, gold answer, and correctness.

## Workflow

1. Load GSM8K JSONL examples with `scripts/answer_tools.py load-jsonl`.
2. Extract final answers from `####` markers.
3. Canonicalize numeric strings by removing commas and normalizing integer-valued decimals.
4. Validate calculator annotations with a restricted arithmetic evaluator.
5. Label candidate solutions by comparing their extracted final answer to the ground truth answer.

## Validation

Run:

```bash
python scripts/answer_tools.py self-test
python tests/test_answer_tools.py
```

The Distiller tree validator can also run the tests:

```bash
python /share/project/yuyang/workspace/Paper2Skills/Distiller/skills/module-to-skill/scripts/validate_skill_tree.py . --run-tests
```

## Limitations

This skill intentionally follows the paper's final-answer labeling rule. A solution with flawed reasoning but the correct final answer is labeled correct for verifier-training purposes, while calculator validation remains a separate diagnostic.
