---
name: toxigen_alice_decoding
description: Apply ToxiGen ALICE classifier-in-the-loop weighted beam scoring for adversarial or detoxifying generation experiments.
---

# ToxiGen ALICE Decoding

Use this skill when a task needs ALICE-style candidate ranking or a small classifier-in-the-loop decoding trace. It is suitable for reduced recovery with deterministic fake language models/classifiers and for auditing whether a full generation harness uses the paper's scoring rule.

Do not use this skill to construct demonstration prompts, compute human annotation classes, or train classifiers. It expects candidate continuations and classifier scores to be supplied by the caller.

## Inputs

- Prompt text and optional current prefix.
- Candidate continuations with language-model log probabilities.
- Classifier log probabilities for `toxic` and `benign` classes for each candidate.
- `prompt_label`, `attack` mode, `lambda_l`, `lambda_c`, and beam size.
- Optional prompt-copy exclusion.

## Outputs

- Selected continuation and ranked beam records.
- Per-candidate trace containing LM log probability, target class, classifier log probability, combined score, and excluded status.
- Mechanism flags for recovery: weighted scoring used, classifier target used, and prompt-copy prevention used.

## Workflow

1. Map the attack mode and prompt label to the classifier class to maximize.
2. Remove prompt-copy candidates if configured.
3. Compute `lambda_l * lm_logprob + lambda_c * classifier_logprob[target_class]`.
4. Sort candidates by combined score and keep the requested beam size.
5. Emit a trace that allows analysis to verify the mechanism independently of metric success.

## Validation

Run:

```bash
python scripts/alice_decoding.py --self-test
python tests/test_alice_decoding.py
```

The tests check target-class mapping, classifier-dominated selection, and prompt-copy exclusion.

## Limitations

This skill does not call GPT-3, HateBERT, or external APIs. In full recovery, callers should pass real model scores. In soft reduced recovery, deterministic scores are acceptable only when the result is explicitly marked as a proxy.
