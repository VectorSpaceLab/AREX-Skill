---
name: gsm8k_candidate_generation
description: Build diverse GSM8K candidate solution records and label them by final-answer agreement for verifier training.
---

# GSM8K Candidate Generation

Use this skill when constructing verifier-training or recovery inputs for the GSM8K verifier pipeline. It creates multiple candidate solutions per problem and labels them with the final-answer rule.

Do not use this skill to claim real language-model sampling unless a real generator produced the candidates. Deterministic perturbations are reduced recovery evidence and must be declared as such.

## Inputs

- GSM8K examples with `question` and `answer`.
- Access to the answer tools script.
- Candidate source mode, such as `gold_and_perturb`.

## Outputs

- Candidate records with problem id, solution, extracted answer, label, and source.
- Diversity summaries with positive and negative counts per problem.

## Workflow

1. Read a bounded list of GSM8K examples.
2. Emit the gold solution as a positive candidate.
3. Emit deterministic perturbed final-answer candidates as negatives.
4. Use `gsm8k_answer_tools` to extract answers and assign labels.
5. Record diversity counts so recovery can prove that ranking is meaningful.

## Validation

Run:

```bash
python scripts/candidate_generation.py self-test
python tests/test_candidate_generation.py
```

## Limitations

The deterministic candidate generator is for reduced recovery and testing. Full paper-scale use should replace the candidate policy with completions sampled from a finetuned generator while keeping the same record and label contract.
