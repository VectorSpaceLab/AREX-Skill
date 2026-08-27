---
name: "training-evaluation-deployment"
description: "Chronos-2 fine-tuning, training configs, evaluation workflows,
  aggregate relative scores, and SageMaker deployment references."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# training-evaluation-deployment

Use this sub-skill for Chronos non-inference workflows:
- Chronos-2 `fit()` and LoRA/full fine-tuning
- original Chronos training configs and KernelSynth data generation
- `fev`-based evaluation and aggregate relative scores
- SageMaker deployment shape, payloads, and reference-only cloud constraints

## Route elsewhere
- Forecast usage and output interpretation: `../chronos-2-forecasting/` or `../chronos-bolt-and-original/`
- DataFrame schema, covariates, and validation: `../data-formats-and-validation/`
- Full benchmark reproduction, cloud endpoint execution, and large GPU runs stay reference-only unless the user explicitly supplies credentials, hardware, and time.

## Bundled runtime files
- `references/training-evaluation.md`
- `references/sagemaker-deployment.md`
- `references/troubleshooting.md`
- `scripts/aggregate_relative_scores.py`
- `scripts/chronos2_fit_smoke_template.py`

## Safe defaults
- Scripts do not train, download, or call AWS unless the user explicitly opts in.
- Prefer tiny synthetic data, low step counts, and local outputs for smoke checks.
