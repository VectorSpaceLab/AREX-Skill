---
name: chronos-forecasting
description: "Use Chronos Forecasting for pretrained time-series forecasting,
  Chronos-2 covariates, data validation, fine-tuning, evaluation, and deployment
  planning."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Chronos Forecasting repo skill

Use this repo skill when a task involves the `chronos-forecasting` package, Chronos-2, Chronos-Bolt, original Chronos/T5 time-series forecasting models, probabilistic forecast quantiles, pandas long-format time-series data, covariates, `predict_df`, `predict_fev`, fine-tuning, benchmark evaluation, or deployment planning.

## Install and import check

Base install:

```sh
pip install chronos-forecasting
```

Minimal import check:

```python
import chronos
from chronos import BaseChronosPipeline, Chronos2Pipeline, ChronosBoltPipeline, ChronosPipeline
print(chronos.__version__)
```

Read [references/installation-and-environment.md](references/installation-and-environment.md) before choosing optional extras, GPU wheels, cloud dependencies, or benchmark/training dependencies. Run [scripts/chronos_api_smoke.py](scripts/chronos_api_smoke.py) for a safe import/signature/backend smoke that does not download models by default.

## Choose the route

| User task | Read |
| --- | --- |
| Chronos-2 zero-shot forecasting, multivariate/covariate prediction, `Chronos2Pipeline`, `predict`, `predict_quantiles`, `predict_df`, embeddings, long horizons, or model loading | [sub-skills/chronos-2-forecasting/](sub-skills/chronos-2-forecasting/) |
| DataFrame schema repair, timestamp frequency, future covariate alignment, list-of-dicts validation, preprocessing helpers, or target leakage checks | [sub-skills/data-formats-and-validation/](sub-skills/data-formats-and-validation/) |
| Chronos-Bolt or original Chronos/T5 models, direct quantile vs sample forecasts, univariate tensor/list inputs, or family selection among older model IDs | [sub-skills/chronos-bolt-and-original/](sub-skills/chronos-bolt-and-original/) |
| Chronos-2 fine-tuning/LoRA, original training configs, KernelSynth, fev evaluation, aggregate relative scores, SageMaker/cloud deployment, or side-effecting benchmark/training plans | [sub-skills/training-evaluation-deployment/](sub-skills/training-evaluation-deployment/) |

Shared references:

- Model family comparison and public model IDs: [references/model-overview.md](references/model-overview.md)
- Installation, optional dependencies, CPU/GPU policy, and safe helper list: [references/installation-and-environment.md](references/installation-and-environment.md)
- Cross-cutting failures for imports, loading, optional extras, backend mismatch, and side-effecting workflow gates: [references/troubleshooting.md](references/troubleshooting.md)
- Source snapshot and refresh baseline: [references/repo-provenance.md](references/repo-provenance.md)

## Operating guardrails

- Prefer `BaseChronosPipeline.from_pretrained(...)` when the model anchor may be any Chronos family, then inspect `type(pipeline).__name__` before calling family-specific APIs.
- Do not trigger Hugging Face downloads, S3 downloads, dataset downloads, SageMaker endpoint creation, model training, or hub pushes unless the user explicitly asks and supplies the needed model/data/credential/budget context.
- Keep `prediction_length`, `quantile_levels`, `batch_size`, `context_length`, `device_map`, and dtype explicit in reproducible snippets.
- Validate pandas schemas before disabling `validate_inputs` or accepting a `future_df` with known-future covariates.
- Do not claim GPU, cloud, or benchmark verification from a CPU import smoke. Record those as optional/unverified unless actually executed.
- When using this skill for a different checkout, read [references/repo-provenance.md](references/repo-provenance.md); refresh if the commit, package version, public APIs, or evidence paths changed.
