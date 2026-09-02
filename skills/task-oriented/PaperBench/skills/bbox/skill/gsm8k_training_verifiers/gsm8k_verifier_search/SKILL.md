---
name: gsm8k_verifier_search
description: Select GSM8K answers by ranking verifier-scored candidate solutions or voting among top-ranked answers.
---

# GSM8K Verifier Search

Use this skill when candidate solutions have verifier scores and the experiment needs to select a final answer per GSM8K problem. It implements top-score selection and top-k majority voting.

Do not use this skill to create verifier scores. It only consumes scored candidates.

## Inputs

- Candidate records with `problem_id`, `extracted_answer`, `verifier_score`, and optional `label`.
- Selection mode: `top_score` or `top_k_vote`.
- Top-k value for voting.

## Outputs

- Prediction records with selected answer, selected candidate id, and audit details.
- Ranking and vote metadata.

## Workflow

1. Group scored candidates by problem id.
2. Sort candidates by verifier score with deterministic tie-breaking.
3. Select the top candidate in `top_score` mode.
4. Count final-answer votes among the top `k` ranked candidates in `top_k_vote` mode.
5. Emit predictions ready for solve-rate evaluation.

## Validation

Run:

```bash
python scripts/verifier_search.py self-test
python tests/test_verifier_search.py
```

## Limitations

The skill assumes scores are already comparable within a problem. It does not calibrate scores across models or datasets.
