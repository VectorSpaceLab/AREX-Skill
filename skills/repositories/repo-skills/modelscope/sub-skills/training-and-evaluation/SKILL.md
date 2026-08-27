---
name: training-and-evaluation
description: "Use for ModelScope trainer construction, TrainingArgs conversion,
  fine-tuning and evaluation preflight, checkpoint hooks, and safe train/eval
  command planning."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ModelScope Training and Evaluation

Use this sub-skill when a task asks to train, fine-tune, evaluate, configure, or preflight a ModelScope training job. It focuses on package-level trainer APIs and safe planning. It does not perform long-running training, download models or datasets, or verify broad CUDA/domain recipes by itself.

## Read this when

- The user needs `build_trainer(name, default_args)` or an `EpochBasedTrainer`-style workflow.
- The user has CLI-like fine-tuning flags and wants the effective ModelScope config before launch.
- The user needs a config-file shape for `train`, `evaluation`, optimizer, LR scheduler, hooks, checkpointing, or distributed launch.
- The user is adapting a ModelScope example recipe but still needs model/data/cache/GPU preflight.
- The user asks about `modelscope.tools.train` or `modelscope.tools.eval` command shape.

## Route elsewhere

- For inference from a trained checkpoint or exported model, read `../pipelines-and-models/SKILL.md`.
- For `MsDataset.load`, local dataset recipes, config file parsing, or file IO details, read `../datasets-config/SKILL.md` first, then return here for trainer wiring.
- For Hub authentication, cache layout, model or dataset snapshot downloads, and offline/local-files-only planning, use `../hub-and-cli/SKILL.md`.
- For serving, export, checkpoint conversion utilities, or vLLM/server launch, use `../serving-export-and-tools/SKILL.md`.
- For implementing new ModelScope trainer classes or repository contribution tests, use `../customization-and-development/SKILL.md`.

## Primary references and helper

- Read `references/workflows.md` for safe end-to-end training/evaluation recipes, preflight checklists, API and real-job CLI command shapes.
- Read `references/training-args-reference.md` for `TrainingArgs`, `parse_cli`, `to_config`, config-node mapping, flattened optimizer/LR scheduler values, and dataset column mapping details.
- Read `references/troubleshooting.md` for symptoms, likely causes, and recovery steps for trainer construction, data/config errors, checkpoints, distributed launch, and optional GPU/domain failures.
- Run `scripts/build_training_args_preview.py --help` to inspect the bundled safe preview tool. The helper parses TrainingArgs-style flags and prints the effective config summary without importing ModelScope, downloading models, reading datasets, writing files, or launching training.

## Safe default workflow

1. Identify whether the task is **preview/config planning**, **real training**, **real evaluation**, or **checkpoint/inference handoff**.
2. For preview/config planning, run the bundled helper with the proposed flags. Prefer previewing before writing a config file or launching any train/eval command.
3. For real training/evaluation, require the user or environment to supply all external resources first: local model cache or trusted model id, dataset access or local files, optional extras, credentials, GPU/VRAM if needed, and a writable work directory.
4. Build the trainer only after checking the config, dataset columns, metrics, checkpoint strategy, and backend requirements.
5. Treat any CUDA, DeepSpeed, Megatron, vLLM, TensorFlow, audio/CV/NLP domain-extra execution, or large-model fine-tuning as optional and unverified for this production scope unless a later task explicitly verifies it in the target environment.

## Minimal API pattern

```python
from modelscope.trainers import build_trainer

kwargs = dict(
    model="local-model-dir-or-trusted-model-id",
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    max_epochs=1,
    work_dir="./work_dir",
)
trainer = build_trainer(name="trainer", default_args=kwargs)
trainer.train()
metrics = trainer.evaluate()
```

Important safety notes:

- Passing a remote model id can trigger model/config access and optional remote-code/plugin checks. Use a local model directory or a verified cache when operating offline or in restricted environments.
- `build_trainer` accepts `name='trainer'` and `default_args=None` by default; task-specific trainers use registered names such as NLP, CV, audio, or multi-modal trainer ids.
- `trainer.train()` and `trainer.evaluate()` are real execution calls. Do not run them as a harmless smoke test.

## Real-job command shapes

These commands are documented here only so an agent can recognize or prepare them. They launch real jobs and can download models, allocate GPUs, read datasets, and write checkpoints/logs.

```bash
python -m modelscope.tools.train CONFIG_PATH TRAINER_NAME
python -m modelscope.tools.eval CONFIG_PATH --trainer_name TRAINER_NAME --checkpoint_path CHECKPOINT_PATH
```

Before using either command, complete the preflight in `references/workflows.md` and preview TrainingArgs-derived config with the bundled helper when the job is being constructed from flags.

## Evidence basis

This sub-skill distills public behavior from the README training example, trainer builder and trainer implementation, TrainingArgs and CLI argument parser implementation, hook/checkpoint/distributed trainer modules, train/eval tool modules, representative PyTorch finetuning examples, the TrainingArgs unit test, and repository developer test-level guidance. Source paths are evidence only; future agents should use the bundled references and helper instead of reopening the original checkout.
