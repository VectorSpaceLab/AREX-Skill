---
name: privacy-tests
description: "Routes TensorFlow Privacy users who want membership inference
  analysis, privacy reports, membership inference callbacks, or secret-sharer
  exposure checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Privacy tests

Use this sub-skill when the user wants to measure memorization or privacy risk from model outputs.

## Trigger phrases

- "membership inference"
- "privacy report"
- "attack results"
- "epsilon lower bound"
- "privacy callback"
- "secret sharer"
- "exposure"
- "memorization"

## What this sub-skill covers

- `AttackInputData`, `SlicingSpec`, and `AttackType`
- `run_attacks()`, `run_membership_probability_analysis()`, and `run_attack_on_keras_model()`
- `MembershipInferenceCallback` and the `keras_evaluation` callback path
- `AttackResults`, privacy-report metadata, and pandas summaries
- `privacy_report` plotting/report helpers
- secret-sharer secret generation and exposure computation

## What it does not cover

- DP training or optimizer selection -> `../training/`
- privacy budget and epsilon/noise search -> `../privacy-accounting/`
- `DPQuery` internals -> `../queries/`
- fast clipping internals -> `../fast-clipping/`

## Read this before you act

- `references/api-reference.md` for attack inputs, outputs, and the bundled smoke pattern.
- `references/troubleshooting.md` for tiny-data, shape, and dependency failures.
- `../../references/install-and-scope.md` for the minimum CPU runtime.

## Typical workflow

1. Decide whether the user wants membership inference or secret-sharer exposure analysis.
2. Build the smallest valid `AttackInputData` or secret-sharer fixture.
3. Use the bundled smoke helper before trying a larger analysis.
4. If the user is asking for training guidance rather than analysis, route to `training`.

## Bundled helpers

- `scripts/tiny_mia_smoke.py` runs a threshold membership-inference attack on synthetic losses.
- `scripts/tiny_secret_sharer_smoke.py` generates a toy secret set and computes exposure on synthetic perplexities.
