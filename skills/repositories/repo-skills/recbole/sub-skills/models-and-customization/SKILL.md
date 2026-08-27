---
name: models-and-customization
description: "Select RecBole model families and implement or diagnose custom
  RecBole models, trainers, dataloaders, samplers, and metrics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# RecBole Models And Customization

Use this sub-skill when the user asks which RecBole model family to use, why a
model cannot be resolved, how to implement a custom recommender component, or
how model choice constrains required data files and optional dependencies.

## Route Here For

- Selecting among general, sequential, context-aware/CTR, knowledge-aware, and
  external-library models.
- Choosing examples such as `BPR`, `LightGCN`, `SASRec`, `GRU4Rec`, `FM`,
  `DeepFM`, `KGAT`, `KGIN`, `XGBoost`, or `LightGBM`.
- Diagnosing `get_model(model_name)` or `get_trainer(model_type, model_name)`
  failures, including case-sensitive class names and missing property defaults.
- Sketching or reviewing custom subclasses of `GeneralRecommender`,
  `SequentialRecommender`, `ContextRecommender`, or `KnowledgeRecommender`.
- Deciding whether a custom trainer, dataloader, sampler, or metric is needed.

## Operating Workflow

1. **Classify the recommendation task.** Use
   [model-families-and-selection.md](references/model-families-and-selection.md)
   before suggesting a model. A CTR request with labels or side features is a
   context-aware task, not a plain general recommender, unless the user
   explicitly wants to ignore those features.
2. **Check data prerequisites early.** General and sequential tasks are driven
   by `.inter`; CTR/context-aware tasks usually need `.inter` labels and may
   need `.user`/`.item`; knowledge-aware tasks need `.inter`, `.kg`, and
   `.link`. Route atomic-file schema, config priority, and validation details to
   the sibling `configuration-and-data` sub-skill.
3. **Resolve the model registry.** Prefer public class spellings such as `BPR`,
   `SASRec`, `FM`, `KGAT`, `XGBoost`, and `LightGBM`. Use the bundled helper
   `scripts/inspect_model_registry.py` to inspect an installed package without
   relying on a repository checkout.
4. **For custom models, enforce the RecBole contract.** Select the correct base
   recommender, set `input_type`, implement `__init__`, `calculate_loss`, and
   `predict`, optionally implement `full_sort_predict`, and read all custom
   hyperparameters from `config`. See
   [customization-guide.md](references/customization-guide.md).
5. **For custom execution behavior, decide the extension point.** Use a custom
   trainer for optimization/evaluation loop changes, a dataloader for batch
   structure changes, a sampler for negative-sampling policy changes, and a
   metric for evaluator output changes. Route actual fitting, evaluation, HPO,
   checkpoints, and case-study execution to `training-evaluation-and-tuning`.
6. **Troubleshoot from the symptom.** Use
   [troubleshooting.md](references/troubleshooting.md) for model-name,
   dependency, `input_type`, missing method, family/data mismatch, and GPU/OOM
   issues.

## Bundled Helper

- `scripts/inspect_model_registry.py`: prints the installed RecBole version,
  resolves one or more model names with `get_model`, reports trainer resolution,
  and optionally prints constructor signatures, MRO, module names, and known
  property-YAML filenames. It accepts `--properties-dir` when the user wants to
  inspect a specific model-properties directory.

## Boundaries

- Do not run training, evaluation, HPO, checkpoints, or case studies here; use
  `training-evaluation-and-tuning`.
- Do not deep-dive atomic file schemas, config precedence, dataset conversion,
  or data validation here; use `configuration-and-data`.
- Do not produce exhaustive model catalogs. Summarize families, show durable
  examples, and verify ambiguous names with the installed-package helper.
