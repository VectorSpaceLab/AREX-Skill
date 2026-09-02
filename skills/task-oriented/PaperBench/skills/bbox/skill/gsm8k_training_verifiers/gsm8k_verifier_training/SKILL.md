---
name: gsm8k_verifier_training
description: Train a deterministic lightweight verifier on correctness-labeled GSM8K candidate solutions and record loss traces.
---

# GSM8K Verifier Training

Use this skill when a GSM8K recovery or experiment needs a learned candidate scorer but the full paper model stack is unavailable. It trains a small logistic verifier with deterministic features and gradient descent.

Do not present this as full GPT-3 verifier training. It is a reduced mechanism test unless connected to a real language model verifier.

## Inputs

- Candidate records with binary `label` values.
- Candidate text, calculator checks, and extracted answers.
- Learning rate and step count.

## Outputs

- Trained verifier parameters.
- Loss before and after training.
- Scored candidate records.
- Validator-compatible trace fields: `params_before`, `params_after`, `loss_before`, and `loss_after`.

## Workflow

1. Extract numeric features from each candidate.
2. Initialize weights and bias deterministically.
3. Compute binary cross-entropy loss.
4. Run one or more gradient-descent steps.
5. Save parameters, loss, and scores.

## Validation

Run:

```bash
python scripts/verifier_training.py self-test
python tests/test_verifier_training.py
```

## Limitations

The feature set is intentionally simple and inspectable. It exists to prove a trainable verifier mechanism in reduced recovery, not to match the full-scale neural verifier's generalization.
