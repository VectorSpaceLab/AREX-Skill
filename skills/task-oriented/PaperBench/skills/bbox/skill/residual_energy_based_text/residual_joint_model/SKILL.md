---
name: residual_joint_model
description: Compute residual EBM sequence scores and normalized importance weights from fixed LM proposal log probabilities and scalar energies.
---

# Residual Joint Model

Use this skill when implementing a residual energy-based text model where a fixed locally normalized language model proposes whole continuations and a sequence-level energy model corrects their probabilities.

Do not use this skill to train the base language model, normalize token-level vocabulary distributions, or read the original paper repository. It only handles sequence-level residual scoring and candidate-set normalization.

## Inputs

- `prefix`: context shared by all candidate continuations.
- `candidates`: records with `id`, `text`, optional `lm_logprob`, and required `energy`.
- Optional score mode:
  - `joint`: rank by `lm_logprob - energy`.
  - `energy`: rank by `-energy` when proposal log probabilities are unavailable.

## Outputs

- Per-candidate `joint_logscore` when `lm_logprob` is present.
- Per-candidate unnormalized and normalized importance weights proportional to `exp(-energy)`.
- Stable ranking and selected candidate id.

## Workflow

1. Keep base-LM log probabilities immutable. They represent the fixed proposal distribution from the paper.
2. Compute residual joint log scores as `lm_logprob - energy`.
3. Compute normalized importance weights with a log-sum-exp transformation over `-energy`.
4. Select by joint score when proposal log probabilities are available; otherwise select by normalized energy weight.
5. Record whether a result used full joint scoring or energy-only reweighting.

## Validation

Run:

```bash
python scripts/residual_joint.py --demo
python -m pytest tests
```

The tests verify exact score arithmetic, stable normalization, and deterministic selection.

## Limitations

Candidate-set normalization is not the full partition function over all text. It is valid as proposal-sample reweighting evidence or as a reduced proxy, not as a full perplexity claim unless the proposal sample size and estimator protocol match the paper target.

