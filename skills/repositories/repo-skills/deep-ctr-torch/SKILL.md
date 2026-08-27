---
name: deep-ctr-torch
description: "Use DeepCTR-Torch for PyTorch CTR/recommender feature columns,
  single-task models, DIN/DIEN sequence models, and multi-task learning
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# DeepCTR-Torch

Use this repo skill when a task names **DeepCTR-Torch**, `deepctr_torch`, `deepctr-torch`, PyTorch CTR prediction, recommender ranking models, `SparseFeat`/`DenseFeat`, DeepFM-style models, DIN/DIEN behavior histories, or SharedBottom/ESMM/MMOE/PLE multi-task CTR workflows.

DeepCTR-Torch is a PyTorch package for deep-learning based CTR and recommender models. It exposes feature-column classes, model constructors, and Keras-like `compile`/`fit`/`predict`/`evaluate` methods.

## Install and import

Prefer an isolated Python environment. Minimal package install:

```bash
python -m pip install -U deepctr-torch
python - <<'PY'
import deepctr_torch
from deepctr_torch.inputs import SparseFeat, DenseFeat, VarLenSparseFeat, get_feature_names
from deepctr_torch.models import DeepFM
print(deepctr_torch.__version__)
PY
```

If `import deepctr_torch` fails with `ModuleNotFoundError: requests`, install `requests` explicitly; the package imports it for a best-effort version check even though the distribution metadata may not declare it.

Run the bundled environment checker when starting from an unfamiliar environment:

```bash
python scripts/check_deepctr_torch_env.py --quick
```

## Route map

| User task | Load |
| --- | --- |
| Build `SparseFeat`, `DenseFeat`, `VarLenSparseFeat`, `feature_names`, or `model_input` dictionaries from tabular data | [feature-column-inputs](sub-skills/feature-column-inputs/SKILL.md) |
| Validate sparse ids, dense vector widths, sequence padding, `length_name`, shared `embedding_name`, or batch sizes | [feature-column-inputs](sub-skills/feature-column-inputs/SKILL.md) |
| Train or predict with DeepFM, WDL, xDeepFM, AFM, AFN, AutoInt, DCN, DCNMix, FiBiNET, IFM, DIFM, MLR, NFM, ONN, PNN, or CCPM | [single-task-modeling](sub-skills/single-task-modeling/SKILL.md) |
| Convert a binary CTR example to regression, choose losses/metrics, use callbacks, save/load weights, or debug single-target training | [single-task-modeling](sub-skills/single-task-modeling/SKILL.md) and [training API](references/training-api-and-persistence.md) |
| Build DIN/DIEN behavior-history models, align `hist_*` features, share embeddings, set `seq_length`, or use DIEN negative sampling | [sequence-and-interest-models](sub-skills/sequence-and-interest-models/SKILL.md) |
| Use pooled multi-value inputs such as genre lists without DIN/DIEN attention | [feature-column-inputs](sub-skills/feature-column-inputs/SKILL.md), then [sequence-and-interest-models](sub-skills/sequence-and-interest-models/SKILL.md) if sequence-specific behavior is needed |
| Train SharedBottom, ESMM, MMOE, or PLE with multiple targets | [multitask-modeling](sub-skills/multitask-modeling/SKILL.md) |
| Troubleshoot install/import, offline version checks, GPU selection, data shapes, callbacks, metrics, or PyTorch compatibility | [troubleshooting](references/troubleshooting.md) |
| Check whether this skill matches a repository checkout or package version | [repo provenance](references/repo-provenance.md) |

## Common operating pattern

1. Build and validate feature columns in `feature-column-inputs`.
2. Choose the model route: single-task, sequence-interest, or multi-task.
3. Compile with supported optimizer/loss/metric strings from [training API](references/training-api-and-persistence.md).
4. Fit on a `model_input` dictionary whose keys exactly match `get_feature_names(...)`.
5. Predict and evaluate by task type; for multi-task outputs, evaluate each prediction column against the matching `task_names` entry.
6. Use bundled smoke scripts from the owning sub-skill to verify installation or reproduce a minimal pattern before scaling to real data.

## Backend notes

DeepCTR-Torch supports CPU workflows and optional PyTorch CUDA devices via `device='cuda:0'` and, for DataParallel, `gpus=[0, 1]`. The generated skill was verified for CPU package inspection and tiny CPU training/prediction smokes. Treat GPU and multi-GPU execution as optional unless a user explicitly requests backend verification.

## Boundaries

This skill teaches package use, not model-quality benchmarking or recommender-system theory. It does not replace feature engineering, data leakage checks, calibration, or production serving validation. It does not cover arbitrary custom multi-task graph architectures beyond the four package classes.
