---
name: importance_sampling_generation
description: Estimate residual EBM partition terms and select text continuations by importance reweighting fixed-LM proposal samples.
---

# Importance Sampling Generation

Use this skill when evaluating or generating from a residual text EBM with a fixed language-model proposal. It provides the paper's practical mechanism for avoiding MCMC over discrete text.

Do not use this skill to claim full perplexity from a tiny sample set. Small candidate sets are reduced/proxy evidence unless they match the paper's estimator scale and data protocol.

## Inputs

- Candidate continuations sampled from the fixed base LM.
- Energy scores for each continuation.
- Optional base-LM log probabilities for residual joint ranking.
- Optional token count and target continuation for a reduced perplexity-style calculation.

## Outputs

- `log_z_estimate`: sample estimate of `log E_{P_LM}[exp(-E)]`.
- Normalized weights proportional to `exp(-E)`.
- Selected continuation by energy-only importance weight for generation, with residual joint score retained as a diagnostic when base-LM log probabilities are available.
- Effective sample size and concentration diagnostics.

## Workflow

1. Compute stable `log mean exp(-energy)` across proposal samples.
2. Normalize `exp(-energy)` into candidate weights.
3. Select the best deterministic candidate by normalized `exp(-E)` weight, using proposal log probability only as a tie-break when energy weights are exactly tied. Keep `lm_logprob - energy` as an evaluation/ranking diagnostic, not the default generation selector.
4. Report effective sample size so inefficient proposal search is visible.
5. Keep proposal provenance separate from residual-energy scoring.

## Validation

Run:

```bash
python scripts/importance_sampling.py --demo
python -m pytest tests
```

The tests verify stable log-mean-exp behavior, normalized weights, increased weight for lower energy, and generation selection by energy weight even when a negative candidate has a high proposal log probability.

## Limitations

Importance sampling quality depends on proposal coverage. A poor base LM can make residual search inefficient, exactly as the paper notes. Record sample count and proposal source in recovery artifacts.
