---
name: pipelines
description: "Guides DeepPavlov configuration, CLI, training, evaluation,
  registry, and custom-component workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Pipelines

Use this sub-skill for DeepPavlov’s configuration-driven workflows: building a
pipeline, training or evaluating it, inspecting config dependencies, and
extending the registry with custom components or metrics.

## Owns

- CLI modes: `install`, `download`, `train`, `evaluate`, `interact`, `predict`,
  and `crossval`.
- Python APIs: `build_model`, `train_model`, `evaluate_model`,
  `train_evaluate_model_from_config`, `read_data_by_config`,
  `get_iterator_from_config`, `parse_config`, and `deep_download`.
- Config mechanics: `chainer.in`, `chainer.out`, `chainer.pipe`, `in`, `out`,
  `in_y`, `id`, `ref`, nested `config_path`, `overwrite`,
  `metadata.variables`, `metadata.imports`, and `metadata.requirements`.
- Training config mechanics: `dataset_reader`, `dataset_iterator`, `train`,
  `metrics`, `fit_on`, `save_path`, `load_path`, `main`, and `recursive`.
- Registry and metric extension patterns for custom components.

## Does Not Own

- Model-family selection, input/output shapes, and dataset layout choices for
  classifiers, NER, embeddings, ODQA, KBQA, ranking, or SQuAD-style tasks.
  Route those questions to `../text-models/SKILL.md` or
  `../retrieval-qa/SKILL.md`.
- REST or socket serving. Route `riseapi` and `risesocket` questions to
  `../serving/SKILL.md`.
- Cross-cutting install, backend, cache, or download problems that affect the
  whole package. Use the root skill’s troubleshooting reference when the issue
  is not specific to config parsing or training.

## Read This First

1. `references/config-workflows.md` for end-to-end config loading, CLI modes,
   training, evaluation, cross-validation, and parameter search.
2. `references/api-reference.md` for verified public signatures and config-field
   semantics.
3. `references/custom-components.md` for registry, metric, `id`/`ref`, and
   `metadata.imports` workflows.
4. `references/troubleshooting.md` for config, registry, and CLI failure modes.
5. `scripts/inspect_config_requirements.py` when you need a no-download summary
   of a config’s nested pipelines, class names, requirement files, and download
   references.

## Typical Entry Points

- Start with `build_model(<config>)` when you need an inference-ready pipeline.
- Use `train_model(<config>)` when you need a trained Chainer back after the
  training run.
- Use `evaluate_model(<config>)` or
  `train_evaluate_model_from_config(<config>, to_train=False)` when you need
  metrics on the configured validation/test split.
- Use `python -m deeppavlov train <config>` for CLI training, `evaluate` for
  metrics only, and `predict` for stdin/file batch inference.
- Use `python -m deeppavlov.paramsearch <config> --folds ...` for grid search
  over `search_choice` values.
- Use `python -m deeppavlov crossval <config> --folds ...` for plain
  cross-validation over the union of train and validation data.

## Workflow Hints

- If the config name is only a stem, let DeepPavlov resolve it; aliases may be
  mapped to a newer config and emit a warning.
- If a config nests another config with `config_path`, inspect the nested
  config first. `overwrite` uses dot notation, and list positions are numeric
  path segments.
- If a component is shared across branches, give it an `id` and reuse it with
  `ref` or `#id`-style references in later params.
- If a config needs custom code, prefer `metadata.imports` or a fully qualified
  `module.submodule:ClassName` / `module.submodule:function_name` reference.
- If `predict` says to use `interact`, you are on a terminal TTY and should
  switch modes instead of forcing stdin handling.

## Routing Notes

- Use `../../references/troubleshooting.md` for package-wide install/import
  issues once the root skill exists; keep config-specific symptoms here.
- Use the sibling model-family skills for task-specific data shapes and
  backend-heavy model choices.
- Keep this sub-skill focused on how pipelines are wired and executed, not on
  which model family to choose.
