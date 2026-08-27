---
name: training-core
description: "Routes AXLearn trainer configs, fake-data smoke checks, launcher
  usage, and tokenizer setup."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# training-core

Use this sub-skill for AXLearn's shared training machinery:

- `config_for_function`, `config_for_class`, and `Configurable`/`Module` patterns.
- `SpmdTrainer`, `SpmdEvaler`, learners, optimizers, checkpointers, and schedules.
- `axlearn.common.launch_trainer_main` and `axlearn.common.launch_trainer`.
- Fake-data / CPU-safe tutorial workflows such as the logistic-regression example.
- SentencePiece training and tokenizer plumbing when the task is about training setup rather than a specific model family.

If the task names GPT/Fuji/Gala/Honeycrisp/Qwen/MoE, jump to `../language-models/`.
If the task names ImageNet/ResNet/vision models, jump to `../vision-workflows/`.
If the task names ASR/Conformer/LibriSpeech, jump to `../audio-asr/`.
If the task names `axlearn gcp ...`, jump to `../cli-cloud/`.

## What to read

- `references/workflows.md` for trainer and fake-data workflows.
- `references/troubleshooting.md` for install/import/config pitfalls.
- `scripts/inspect_trainer_config.py` for a safe config-inspection helper.

## Typical workflows

### Inspect a trainer config

Use this when you want to see what a named trainer config resolves to without launching a long run:

```bash
python scripts/inspect_trainer_config.py --module axlearn.experiments.logistic_regression.tutorial --config LogisticRegression
```

### Run a CPU-safe tutorial smoke check

The logistic-regression tutorial is the best small local probe because it uses synthetic data and a short config path:

```bash
DATA_DIR=FAKE python -m axlearn.common.launch_trainer_main \
  --module=axlearn.experiments.logistic_regression.tutorial \
  --config=LogisticRegression \
  --trainer_dir=/tmp/axlearn-logreg \
  --data_dir=FAKE \
  --jax_backend=cpu
```

### Inspect launcher helpers

When debugging launcher behavior, check the shared trainer entrypoints rather than the experiment module first:

- `axlearn.common.launch_trainer_main`
- `axlearn.common.launch_trainer.get_trainer_config`
- `axlearn.common.trainer.SpmdTrainer`

### SentencePiece training

Use this sub-skill for tokenizer setup when the user is creating or validating a sentencepiece model. The command is CPU-oriented and can be memory-hungry, so treat it as a setup workflow, not a quick unit test.

## Decision points

- Prefer fake-data or synthetic-data configs when the goal is to validate wiring.
- Prefer named trainer configs when the goal is to inspect config composition or mesh settings.
- Do not route GPT-family catalogs here if the task specifically names Fuji, Gala, Honeycrisp, Qwen, MoE, or flash attention.
- Do not route cloud launch/bundle behavior here; that belongs to `cli-cloud`.
