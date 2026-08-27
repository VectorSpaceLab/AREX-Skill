---
name: nni
description: "Use NNI for AutoML experiments, hyperparameter tuning, neural
  architecture search, model compression, feature engineering, nnictl, and
  optional dependency troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# NNI

Use this repo skill when the user asks about Microsoft NNI / Neural Network Intelligence: AutoML experiments, hyperparameter optimization, neural architecture search, model compression, feature engineering, `nnictl`, trial APIs, search spaces, training services, or NNI optional dependency failures.

## Start Here

1. Identify the user-facing workflow from the request: HPO experiment, NAS, compression, feature engineering/utilities, or install/runtime troubleshooting.
2. Run `scripts/check_nni_environment.py --format text` when the user reports import, `nnictl`, package metadata, or optional dependency problems.
3. Route to the focused sub-skill before writing detailed code or configs.
4. Use bundled validators for static checks instead of running training, cloud services, notebooks, benchmarks, or downloads by default.
5. Read `references/repo-provenance.md` before deciding whether this skill is current for a different NNI checkout.

## Route By Task

| User task or signal | Use |
| --- | --- |
| `nnictl`, experiment YAML, `ExperimentConfig`, `Experiment`, trial code, search-space JSON, tuners, assessors, training services | `sub-skills/hpo-experiments/` |
| `ModelSpace`, `LayerChoice`, `InputChoice`, NAS evaluator, NAS strategy, `NasExperiment`, fixed architecture export | `sub-skills/nas/` |
| pruning, quantization, distillation, compression `config_list`, pruners, quantizers, evaluators, speedup/export | `sub-skills/model-compression/` |
| `GBDTSelector`, `FeatureGradientSelector`, `nni.trace`, `nni.dump`, concrete tracing, graph/profiler/flop utilities | `sub-skills/feature-engineering-and-utilities/` |
| import/install failures, package version, missing optional stacks, `pkg_resources`, broad NNI task classification | this root skill plus `references/troubleshooting.md` |

## Quick Install And Import Checks

For normal users, start from a released package:

```bash
python -m pip install nni
python -c "import nni; print(nni.__version__)"
nnictl --help
```

For source-development workflows, NNI packaging can involve generated frontend assets in addition to Python modules. If editable installation from a checkout fails on missing node/frontend package material, either build the frontend according to the source-build docs or use the Python source tree for read-only API inspection while treating Web UI assets as unavailable.

## Sub-skills

### HPO Experiments

Read `sub-skills/hpo-experiments/SKILL.md` when the request mentions HPO, experiment configs, search spaces, `nnictl`, trial metric reporting, tuners, assessors, or training services.

Useful bundled entry points:

- `sub-skills/hpo-experiments/references/workflows.md` for CLI and Python experiment recipes.
- `sub-skills/hpo-experiments/references/api-reference.md` for trial, tuner, assessor, and search-space API facts.
- `sub-skills/hpo-experiments/references/cli-reference.md` for `nnictl` command families.
- `sub-skills/hpo-experiments/scripts/validate_search_space.py` for dependency-free JSON search-space validation.

### NAS

Read `sub-skills/nas/SKILL.md` when the request mentions NAS model spaces, mutables, evaluators, strategies, model export/freeze, or `torch` / `pytorch_lightning` import failures while doing NAS.

Useful bundled entry points:

- `sub-skills/nas/references/workflows.md` for model-space, evaluator, strategy, and fixed-architecture workflows.
- `sub-skills/nas/references/api-reference.md` for key object names and optional dependency boundaries.
- `sub-skills/nas/scripts/check_nas_optional_deps.py` for safe optional-stack diagnostics.

### Model Compression

Read `sub-skills/model-compression/SKILL.md` when the request mentions NNI pruning, quantization, distillation, `config_list`, evaluator wrappers, speedup, or export.

Useful bundled entry points:

- `sub-skills/model-compression/references/workflows.md` for pruning, quantization, distillation, evaluator, and speedup flows.
- `sub-skills/model-compression/references/api-reference.md` for config-list and compression API contracts.
- `sub-skills/model-compression/scripts/validate_config_list.py` for dependency-free JSON config-list validation.

### Feature Engineering And Utilities

Read `sub-skills/feature-engineering-and-utilities/SKILL.md` when the request mentions feature selectors, trace serialization, concrete tracing, graph inspection, FLOP/profiler helpers, or utility import problems.

Useful bundled entry points:

- `sub-skills/feature-engineering-and-utilities/references/workflows.md` for selector and utility recipes.
- `sub-skills/feature-engineering-and-utilities/references/api-reference.md` for selected import paths and data expectations.
- `sub-skills/feature-engineering-and-utilities/scripts/check_optional_utilities.py` for safe utility-stack diagnostics.

## Cross-cutting Troubleshooting

Read `references/troubleshooting.md` when the request is about installation, package metadata, `nnictl` entry points, `pkg_resources`, missing optional dependencies, source-build frontend assets, version mismatch, or deciding which optional stack is required.

Use these defaults:

- Do not install broad optional extras unless the user explicitly needs many optional algorithms; prefer the specific extra or package named by the failing workflow.
- Do not run remote/cloud training services, notebooks, benchmarks, full NAS searches, compression training, or dataset downloads without explicit user approval.
- Treat `torch`, `pytorch_lightning`, LightGBM, Transformers, DeepSpeed, TensorRT, ONNX, and cloud credentials as optional workflow dependencies, not base NNI requirements.
- Prefer static validators and import diagnostics before suggesting expensive runtime execution.

## Provenance And Refresh

Read `references/repo-provenance.md` if a user asks whether this skill matches a current NNI checkout. If the commit, package version, source roots, public entry points, documentation, examples, or tests have changed, refresh the repo skill before relying on detailed guidance.
