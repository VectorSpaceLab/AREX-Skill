# NAS Troubleshooting

## Quick Diagnostic

Run the bundled optional dependency checker before debugging deep NAS failures:

```bash
python scripts/check_nas_optional_deps.py
python scripts/check_nas_optional_deps.py --format json
```

The script only imports modules and reports guidance. It does not train, download data, launch `nnictl`, or mutate files.

## `No module named 'torch'`

Symptoms:

- `import nni.nas.nn.pytorch` fails.
- `from nni.nas.nn.pytorch import ModelSpace` fails.
- Hub model spaces under `nni.nas.hub.pytorch` fail.

Likely cause: NNI NAS Retiarii model-space support is PyTorch-centered, and the PyTorch optional stack is not installed in the active environment.

Action:

- Keep the NAS design conceptual if the user only needs scaffolding.
- If execution is required, install a PyTorch build compatible with the user's Python, CUDA, and platform policy.
- Do not switch to TensorFlow for Retiarii NAS unless the user is explicitly working with legacy/non-Retiarii code; current Retiarii NAS is PyTorch-focused.

## `No module named 'pytorch_lightning'`

Symptoms:

- `import nni.nas.evaluator.pytorch` fails.
- Built-in NAS evaluators such as `Classification`, `Regression`, `Lightning`, `LightningModule`, `Trainer`, or `DataLoader` fail to import.
- One-shot strategies cannot be paired with the intended evaluator.

Likely cause: Lightning is optional and was not installed with the minimal NNI package.

Action:

- For multi-trial NAS, use `FunctionalEvaluator` if the user has ordinary training code and does not need Lightning.
- For one-shot NAS, install a compatible `pytorch_lightning` stack or change strategy to multi-trial.
- When writing guidance, say Lightning is required for built-in PyTorch NAS evaluators and one-shot workflows; do not imply it is always present.

## `nni.nas.strategy` Import or Strategy Construction Fails

Symptoms:

- Importing `nni.nas.strategy` fails after a default framework shortcut tries to import PyTorch/Lightning objects.
- `PolicyBasedRL()` raises an error mentioning `tianshou`.
- One-shot strategy construction succeeds but mutation/evaluation fails later.

Action:

- Run the optional dependency checker and inspect per-module failures.
- If `PolicyBasedRL` is requested, check whether `tianshou` is installed; otherwise choose `Random`, `GridSearch`, `RegularizedEvolution`, or `TPE`.
- For one-shot failures, confirm the model space uses supported mutation primitives and the evaluator is Lightning-compatible.

## Evaluator Mismatch

Symptoms:

- A one-shot strategy rejects or breaks with a `FunctionalEvaluator`.
- A custom Lightning evaluator behaves differently under one-shot mutation.
- `nni.report_final_result` is never seen by the strategy.

Likely cause: The evaluator type does not match the strategy or does not report metrics correctly.

Action:

- Multi-trial + existing training loop: prefer `FunctionalEvaluator` and call `nni.report_final_result(metric)`.
- One-shot + shared weights: use `nni.nas.evaluator.pytorch` evaluators or a custom NAS-aware `LightningModule` wrapped by `Lightning`.
- For custom Lightning modules, report intermediate metrics in validation hooks and final metrics when fitting is complete.
- If the user only needs a final fixed model, skip NAS execution and use an exported architecture dict with a normal training loop.

## Serialization Errors and Large Pickles

Symptoms:

- Trial startup fails during serialization.
- Errors mention tracing, pickle size, or inability to reconstruct a dataset/dataloader/transform.
- Multi-trial execution works locally but fails in worker processes.

Likely cause: Evaluator arguments or model-space objects include untraced custom objects.

Action:

- Decorate custom datasets, transforms, factories, and Lightning modules with `nni.trace`.
- Use `nni.nas.evaluator.pytorch.DataLoader` for Lightning evaluators where possible.
- Avoid passing huge in-memory objects as evaluator arguments.
- Rebuild data objects inside a traced factory instead of serializing loaded datasets.

## Model-Space Mutation Errors

Symptoms:

- Errors mention missing labels, duplicate choices, invalid samples, or labels not found in an architecture dict.
- A fixed architecture cannot be reconstructed with `model_context`.
- Shape mismatches occur after `LayerChoice` or `InputChoice` selection.

Action:

- Give every mutable stable labels and keep labels unchanged between search and fixed-model instantiation.
- Use dictionary candidates for `LayerChoice` when exported architecture readability matters.
- Ensure every candidate operation in a `LayerChoice` has compatible input/output tensor shape.
- Ensure `InputChoice` candidates can be reduced by the selected reduction (`sum`, `mean`, `concat`, or `none`).
- With `Repeat`, use factory functions and index-specific labels when each repeated block should choose independently.
- Do not mix legacy mutators with inline primitives such as `LayerChoice` and `nni.choice`.

## Fixed Architecture Does Not Match Search Result

Symptoms:

- `with model_context(exported_arch): MyModelSpace()` does not freeze the same choices.
- `MyModelSpace().freeze(exported_arch)` raises validation errors.
- Retrained final model has unexpected shape or architecture.

Action:

- Confirm the same model-space class and initialization arguments are used for search and final instantiation.
- Confirm labels in the architecture dict match labels declared in the model space.
- Do not edit label names between search and retraining.
- Remember that `export_top_models(formatter="dict")` exports choices, not trained final weights.
- Fully train or evaluate the fixed model on the final data split after exporting choices.

## Benchmark Data Missing

Symptoms:

- `query_nb101_trial_stats`, `query_nb201_trial_stats`, or `query_nds_trial_stats` cannot find databases.
- Errors mention `NASBENCHMARK_DIR`, cache directories, or `peewee`.

Action:

- Confirm the user actually wants benchmark-query mode, not full NAS training.
- Ask before downloading benchmark databases; files can be large.
- Install `peewee` when benchmark database access is required.
- Set `NASBENCHMARK_DIR` before importing NNI if databases are stored outside the default cache.

## GPU, Training Cost, and Dataset Surprises

Symptoms:

- A quick NAS example starts long training.
- Dataset code attempts network downloads.
- One-shot search is slow or OOMs.
- Training service starts more concurrent trials than expected.

Action:

- For smoke tests, reduce `max_trial_number`, `trial_concurrency`, epochs, dataset size, and model width/depth.
- Set `trial_gpu_number = 0` when CPU-only smoke testing is acceptable.
- For one-shot Lightning evaluators, use development settings such as a tiny dataset or Lightning fast-dev mode only as a smoke test, not as a result claim.
- Ask before running dataset downloads, long training, remote training services, or GPU-heavy searches.

## `nnictl` or Generic Experiment Config Confusion

Symptoms:

- The user wants `nnictl` YAML, tuner names, assessor config, or generic HPO trial commands for a NAS task.
- They ask why NAS ignores `search_space`, `trial_command`, or `tuner`.

Action:

- Explain that `NasExperiment` auto-generates the architecture search space and trial command from the model space and strategy.
- Use the HPO/experiment sub-skill for generic experiment lifecycle, `nnictl`, training services, and platform configuration.
- Return here for NAS-specific model-space/evaluator/strategy/export work.

## Source Examples and Notebooks

NNI includes many NAS examples and notebooks, including legacy search-space zoo and DARTS-style tutorials. Treat them as reference patterns only unless the user explicitly approves running them. They can require PyTorch, Lightning, datasets, GPUs, benchmark databases, or long training time.
