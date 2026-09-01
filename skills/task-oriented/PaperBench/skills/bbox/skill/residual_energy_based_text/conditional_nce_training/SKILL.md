---
name: conditional_nce_training
description: Train a tiny residual sequence-energy model with the paper's conditional NCE objective on positive and fixed-LM negative continuations.
---

# Conditional NCE Training

Use this skill when a recovery or implementation needs to exercise the paper's training mechanism: positive human continuations should receive low energy and fixed language-model continuations should receive high energy for the same prefix.

Do not use this skill to update the base language model or to mine negatives from the residual model. The noise distribution is the fixed LM proposal.

## Inputs

- A shared prefix.
- Positive continuation records.
- Negative continuation records sampled or designated as fixed-LM proposal outputs.
- Feature weights for a scalar residual energy function.
- Learning rate and update count.

## Outputs

- NCE loss before and after training.
- Parameters before and after training.
- Positive and negative energy diagnostics.
- A validator-compatible trace showing optimizer state or parameter changes.

## Workflow

1. Encode continuations into deterministic lexical or model-derived features. Include both positive evidence features and artifact features; repeated "quality" terms must not be enough to bypass repetition or coherence penalties.
2. Compute scalar energy as a linear function of those features plus bias.
3. Minimize `softplus(E_positive) + softplus(-E_negative)` averaged over examples.
4. Update only energy parameters.
5. Record the energy gap and loss change; reduced recovery should mark this as reduced training, not full pretrained model training.

## Validation

Run:

```bash
python scripts/nce_train.py --demo
python -m pytest tests
```

The tests verify loss decrease, parameter changes, positive energy lower than negative energy after a bounded deterministic run, and robustness against an adversarial negative that repeats otherwise positive lexical terms.

## Limitations

This skill can run a small deterministic optimizer for recovery evidence. It does not reproduce the paper's large transformer energy network unless a caller supplies that runtime separately and records the environment evidence.
