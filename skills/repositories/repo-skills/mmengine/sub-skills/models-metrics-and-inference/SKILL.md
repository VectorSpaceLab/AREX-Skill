---
name: models-metrics-and-inference
description: "Implement and troubleshoot MMEngine model, metric, evaluator,
  inference, TTA, and model analysis contracts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Models, Metrics, and Inference

Use this sub-skill when a task mentions `BaseModel.forward` modes, `train_step`, `val_step`, `test_step`, `BaseModule` initialization, data preprocessors, `ImgDataPreprocessor`, `BaseMetric`, `Evaluator`, `DumpResults`, `BaseInferencer`, `BaseTTAModel`, `PrepareTTAHook`, or `get_model_complexity_info`.

## Read Order

- [references/model-and-metric-contracts.md](references/model-and-metric-contracts.md): Implement `BaseModel`/`BaseModule`, data preprocessors, step methods, metrics, evaluators, prefixing, CPU-safe result handling, and prediction dumps.
- [references/inference-tta-analysis.md](references/inference-tta-analysis.md): Build inferencer subclasses, configure TTA wrappers/hooks, and use model complexity analysis with realistic runtime limits.
- [references/troubleshooting.md](references/troubleshooting.md): Diagnose common model, metric, evaluator, inference, TTA, and analysis failures by symptom.
- [scripts/model_metric_smoke.py](scripts/model_metric_smoke.py): Run a tiny CPU-only smoke check for `BaseModel`, `BaseModule`, `ImgDataPreprocessor`, `BaseMetric`, `Evaluator`, `DumpResults`, and complexity analysis contracts.
- [scripts/tta_smoke.py](scripts/tta_smoke.py): Run a tiny CPU-only TTA smoke check adapted from MMEngine's documented `BaseTTAModel.merge_preds` pattern without downloads or runner execution.

## Scope

This sub-skill owns `mmengine.model`, `mmengine.evaluator`, `mmengine.infer`, `mmengine.analysis`, TTA model/hook contracts, metric prefixing, prediction dump behavior, and CPU tensor movement caveats.

Route adjacent issues to sibling skills:

- Use `../runner-and-training/SKILL.md` for Runner loop orchestration, train/val/test config placement, hooks outside TTA wrapping, checkpoints, resume, optimizers, schedulers, and launchers.
- Use `../data-structures-and-io/SKILL.md` for dataset records, transforms, collate functions, `BaseDataElement` internals, file IO backends, and sample container details.
- Use `../configuration-and-registry/SKILL.md` for config syntax, registry scopes, `custom_imports`, default scopes, and config-driven build failures.
- Use `../runtime-utilities-and-visualization/SKILL.md` for logger, visualizer backend, message hub, device helper, distributed utility, and service-backed visualization details.

## Fast Workflow

1. Define the data contract first: dataloader/preprocessor output keys, `forward` parameters, prediction object shape, metric inputs, and whether samples are dicts or data elements.
2. Implement `BaseModel.forward` with separate `mode='loss'`, `mode='predict'`, and `mode='tensor'` branches before customizing `train_step`, `val_step`, or `test_step`.
3. Validate metric names early: every `BaseMetric` should use `default_prefix` or an explicit `prefix`, and composed evaluators must not produce duplicate keys.
4. Keep inference and TTA small until contracts pass: a custom inferencer should return serializable predictions by default, and a TTA model should merge one sample's augmented predictions at a time.
5. Use the bundled smoke scripts before debugging larger project code; they exercise MMEngine public APIs without network, credentials, large downloads, or long training.

## Output Expectations

`BaseModel.train_step()` returns log tensors for the runner, while `val_step()` and `test_step()` return predictions consumed by `Evaluator.process()`. `Evaluator.evaluate(size)` returns a metric dictionary, `DumpResults` writes pickle predictions as user project output, inferencers return postprocessed dictionaries, and analysis helpers return complexity dictionaries whose unsupported operators should be reviewed before reporting final numbers.
