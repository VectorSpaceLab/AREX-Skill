---
name: tensorflow-project-template
description: "Guides agents in adapting TensorFlow Project Template
  training-project structure, configs, models, trainers, data loaders,
  TensorBoard logging, checkpoints, and safe smoke checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# TensorFlow Project Template

Use this skill when the task is to understand, copy, modernize, debug, or extend the `Tensorflow-Project-Template` style of TensorFlow project: a model class, trainer class, data generator, JSON config, TensorBoard logger, checkpoint saver, and one `main` entry point wired together.

This repository is a small template, not an installable Python distribution. Treat it as project skeleton guidance: place the project root on `PYTHONPATH` or run from a checkout/copy of the template when validating code.

## First choose the route

| User intent | Use this skill content |
|---|---|
| "How do I add my own model/trainer?" | Read [extension workflow](references/extension-workflow.md), then check API contracts in [API reference](references/api-reference.md). |
| "What config keys and paths does it expect?" | Read [configuration](references/configuration.md). |
| "Why does import/training/logging/checkpointing fail?" | Read [troubleshooting](references/troubleshooting.md), then run `scripts/check_template_static.py`. |
| "Can this copied template still run?" | Run `scripts/check_template_static.py`; if TensorFlow 1.x is installed, run `scripts/run_tiny_training_smoke.py`. |
| "Is this skill current for my checkout?" | Read [repository provenance](references/repo-provenance.md). |

## Runtime assumptions to check first

- The source uses TensorFlow 1.x graph APIs: `tf.Session`, `tf.placeholder`, `tf.variable_scope`, `tf.assign`, `tf.layers.dense`, `tf.train.Saver`, and `tf.summary.FileWriter`.
- A verified legacy runtime used Python 3.7, `tensorflow==1.15.5`, `numpy<1.19`, `tqdm`, `bunch`, and `protobuf<3.20`.
- TensorFlow 2.x does not expose the required top-level symbols by default. If the user wants TensorFlow 2.x, plan a port to `tf.compat.v1` or a full Keras rewrite; do not assume the original files run unchanged.
- No GPU workflow is documented by this repo. CPU is sufficient for the template's example training smoke.
- The inspected source contains TensorBoard logging only. The README mentions Comet.ml, but the checked `Logger` implementation has no Comet import or API call.

## Minimal checks for a copied template project

From this generated skill directory, validate a target checkout or copied project:

```bash
python scripts/check_template_static.py --repo-root /path/to/template-copy
```

If the environment has TensorFlow 1.x-compatible APIs, run a bounded one-step smoke:

```bash
python scripts/run_tiny_training_smoke.py --repo-root /path/to/template-copy --work-dir /path/to/safe-smoke-workdir
```

Both scripts are self-contained skill helpers. They accept an explicit target project path; they do not depend on the original source checkout used to create this skill.

## Template architecture

1. `base/BaseModel` owns shared checkpoint, current-epoch, and global-step behavior. A child model must implement `build_model()` and `init_saver()`.
2. `models/ExampleModel` shows a TF1 graph with placeholders, dense layers, cross-entropy loss, Adam optimizer, accuracy, and a saver.
3. `base/BaseTrain` owns session initialization and epoch looping. A child trainer must implement `train_epoch()` and `train_step()`.
4. `trainers/ExampleTrainer` fetches batches from `DataGenerator`, runs the model train op, summarizes averaged loss/accuracy, and saves a checkpoint each epoch.
5. `data_loader/DataGenerator` is deliberately minimal; replace it with project-specific dataset loading while preserving the `next_batch(batch_size)` contract or update the trainer accordingly.
6. `utils/config.process_config()` reads a JSON config and derives `summary_dir` and `checkpoint_dir` under `../experiments/<exp_name>/` relative to the current process.
7. `mains/example.py` wires config parsing, directory creation, session, data, model, logger, trainer, checkpoint load, and `trainer.train()`.

## When adapting the template

- Start by copying the skeleton model/trainer pattern, not by editing the base classes unless the shared loop/checkpoint contract must change.
- Keep config keys explicit and add new keys to the JSON before using them in model, data, logger, or trainer code.
- Keep tensor shapes aligned: the example model expects `x` shaped `[batch, 784]` and labels shaped `[batch, 10]`.
- For real datasets, make data iteration deterministic enough for small smoke tests before scaling training.
- If adding modern TensorFlow/Keras code, document whether the project remains TF1 graph-mode or becomes TF2 eager/Keras; mixing both silently is a common failure source.

## Bundled references and helpers

- [API reference](references/api-reference.md) records verified classes, methods, and important behavior.
- [Extension workflow](references/extension-workflow.md) gives the end-to-end process for creating a new model/trainer/data pipeline.
- [Configuration](references/configuration.md) lists config keys, derived paths, CLI argument handling, and path gotchas.
- [Troubleshooting](references/troubleshooting.md) maps predictable symptoms to concrete recovery steps.
- [Repository provenance](references/repo-provenance.md) records the source snapshot and evidence paths.
- [Router metadata](references/repo-routing-metadata.json) is structured metadata for managed repo-skill import; do not edit it as prose.
- `scripts/check_template_static.py` validates template files, class hooks, config keys, and TF1 symbol usage without importing TensorFlow.
- `scripts/run_tiny_training_smoke.py` runs an optional one-step training smoke against a target template copy when a TF1-compatible runtime is available.

## Non-goals and cautions

- This skill does not teach generic TensorFlow, Keras, distributed training, dataset APIs, or Comet.ml integration beyond what the repository actually implements.
- Do not tell users that this repo is pip-installable unless their project copy adds packaging metadata.
- Do not run long training, download datasets, or write checkpoints outside an explicit temporary or user-approved work directory.
