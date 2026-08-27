# Training and Evaluation Workflows

## Purpose

Use this reference to plan ModelScope fine-tuning/evaluation jobs safely. It separates safe previews from real launches, summarizes the trainer API and config shape, and distills representative example patterns without requiring access to the original repository examples.

## Safe versus real execution

| Action | Safe by default? | Why |
| --- | --- | --- |
| Run `../scripts/build_training_args_preview.py --help` or preview flags | Yes | It is bundled, deterministic, and does not import ModelScope, download data, create work directories, or launch jobs. |
| Inspect/prepare a config file from user-provided parameters | Usually | Safe if no model/data loading or checkpoint writes occur. |
| Import ModelScope trainer APIs | Usually | Safe if the package and dependencies are installed, but import errors may reveal missing optional deps. |
| `build_trainer(...)` with a local model/config and in-memory datasets | Potentially side-effecting | May create `work_dir`, initialize devices, read configs, construct preprocessors/models, or validate cache state. |
| `trainer.train()` | No | Runs a real training loop, writes logs/checkpoints, may use GPU and large data. |
| `trainer.evaluate()` | No | Loads model/eval dataset and may write prediction or metric artifacts. |
| `python -m modelscope.tools.train ...` / `eval ...` | No | Thin real-job launchers around `build_trainer` plus `train()`/`evaluate()`. |

Default to preview and preflight unless the user explicitly asks to launch a job and has supplied the required model, data, credentials, backend, and output directory choices.

## Preflight checklist before long-running jobs

1. **Task and trainer**
   - Confirm task family and trainer name. Default trainer name is `trainer`; task-specific names include registry ids for NLP, CV, audio, and multi-modal trainers.
   - Confirm whether the user expects a pretrained model config (`use_model_config=True`) or a fully generated/replacement config.
2. **Model source and trust boundary**
   - Prefer a local model directory or verified cache for offline/reproducible work.
   - If using a model id, check revision, cache availability, network policy, and whether remote plugins or `allow_remote` require an explicit `trust_remote_code=True` decision.
   - Route Hub/cache questions to `../hub-and-cli/SKILL.md`.
3. **Data and columns**
   - Confirm train/eval dataset source, split, subset, namespace, and expected columns.
   - Decide whether to use direct `MsDataset.load`, prior `remap_columns`, or a `dataset_json_file` multi-dataset recipe.
   - Route dataset recipe validation to `../datasets-config/SKILL.md`.
4. **Config preview**
   - Use the bundled preview script for base `TrainingArgs`-style flags.
   - Check `train.optimizer`, `train.lr_scheduler`, `train.dataloader`, `evaluation.period`, `evaluation.metrics`, and checkpoint nodes.
5. **Backend and optional dependencies**
   - Confirm PyTorch/TensorFlow/ONNX/domain extras and CUDA availability if required by the model/trainer.
   - Treat broad GPU/domain execution as optional and unverified for this production scope unless separately verified.
6. **Work directory and checkpoint policy**
   - Choose a writable `work_dir` and whether existing files may be overwritten or old checkpoints may be deleted by retention limits.
   - Disable Hub push flags unless credentials and upload side effects are explicitly authorized.
7. **Evaluation and metrics**
   - If `eval_dataset` exists, ensure metrics are configured or that task defaults exist.
   - For best-checkpoint saving, verify `metric_for_best_model` matches the exact metric key emitted by evaluation.
8. **Distributed launch**
   - Do not add distributed hooks casually. DDP, DeepSpeed, Megatron, fp16, and large-model training require matching launch command, env vars, dependencies, GPU/VRAM, and checkpoint format expectations.
9. **Real launch decision**
   - Repeat the final command/API call back to the user with expected writes, external downloads, GPU use, credentials, and stop/resume plan.

## Minimal trainer API recipe

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
# Real execution starts here:
trainer.train()
metrics = trainer.evaluate()
```

Important `default_args` seen in the trainer implementation and examples:

- `model`: local model directory, model id, model object, or model list depending on trainer.
- `cfg_file`: config file path. Required when constructing the default trainer without a pretrained model id.
- `cfg_modify_fn`: callback that receives a config, merges or replaces nodes, and returns the final config.
- `train_dataset`, `eval_dataset`: `MsDataset`, PyTorch dataset, list of datasets, or task-specific custom datasets.
- `data_collator`, `preprocessor`, `optimizers`, `samplers`: advanced customization points.
- `model_revision`, `seed`, `work_dir`, `launcher`, `device`, `efficient_tuners`, `trust_remote_code`: operational settings with optional dependency and side-effect implications.

## Config file shape

A ModelScope training config usually has these top-level areas:

```yaml
framework: pytorch
task: text-classification
model:
  type: text-classification
preprocessor:
  type: sen-cls-tokenizer
  first_sequence: sentence
  label: label
train:
  work_dir: ./work_dir
  max_epochs: 1
  dataloader:
    batch_size_per_gpu: 16
    workers_per_gpu: 0
  optimizer:
    type: AdamW
    lr: 0.00001
  lr_scheduler:
    type: LinearLR
    options:
      lr_strategy: by_epoch
  checkpoint:
    period:
      save_strategy: by_epoch
      interval: 1
evaluation:
  dataloader:
    batch_size_per_gpu: 16
    workers_per_gpu: 0
    shuffle: false
  period:
    eval_strategy: by_epoch
    interval: 1
  metrics: seq-cls-metric
```

Notes:

- The trainer merges default hooks if missing: checkpoint, text logging, and iteration timing.
- Hook-like nested nodes such as `train.logging`, `train.checkpoint.period`, `train.checkpoint.best`, and `evaluation.period` are converted into hook configs by the trainer default-config utilities.
- Config files in Python format can execute code. Prefer JSON/YAML for untrusted content unless a deliberate `trust_remote_code` decision has been made.

## TrainingArgs-to-config workflow

Use this when a user supplies CLI-like flags or adapts a recipe script:

1. Start with the base fields in `references/training-args-reference.md`.
2. Add recipe-specific dataclass fields only when they have clear config nodes, such as `preprocessor.first_sequence`, `preprocessor.label`, `dataset.column_map`, or task-specific scheduler hooks.
3. Parse flags: `args_obj = MyArgs().parse_cli(flag_list)`.
4. Convert: `config, args = args_obj.to_config()`.
5. If `args.use_model_config` is true, merge `config` into the model config inside `cfg_modify_fn`; otherwise replace with the generated config.
6. Preview the effective config before building the trainer.

Safe preview command:

```bash
python scripts/build_training_args_preview.py --max_epochs 1 --lr 1e-5 --format summary
```

## Representative example patterns distilled from public recipes

### README-style GPT fine-tuning pattern

- Load train and eval datasets.
- Remap text columns into the key expected by the model/preprocessor, such as `text1 -> src_txt`.
- Set `model`, datasets, `max_epochs`, and `work_dir` in `default_args`.
- Build a task-specific trainer id and call `trainer.train()`.

This pattern is concise, but it assumes model/data downloads, sufficient accelerator memory for large models, and compatible optional NLP dependencies.

### Text classification pattern

- Extend `TrainingArgs` with `first_sequence`, optional `second_sequence`, `label`, `labels`, and `preprocessor` fields mapped under `preprocessor.*`.
- Derive `label2id` from the train/eval columns when labels are not supplied explicitly.
- Use `use_model_config=True` when fine-tuning a pretrained config and merge only the overrides.
- Set `evaluation.metrics` to a sequence-classification metric and use `eval_strategy`/`eval_interval` to control validation cadence.

### Token classification pattern

- Extend `TrainingArgs` with `first_sequence`, `label`, sequence length, preprocessor type, padding/mode, and trainer/work_dir fields.
- Derive a sorted label list from token-level label arrays and merge both `preprocessor.label2id` and task metric config.
- Validate that `train_dataset[label]` and `validation_dataset[label]` are present and compatible.

### Text generation pattern

- Extend `TrainingArgs` with source/target text keys, trainer id, work_dir, scheduler choice, parallel world size, tensor model parallel size, and a Megatron-hook boolean.
- Map special scheduler aliases into concrete LR scheduler configs in `cfg_modify_fn`.
- Treat Megatron/distributed settings as GPU-only optional execution requiring external verification.

### Multi-modal embedding pattern

- Extend `TrainingArgs` with fp16, optimizer hparams, loss aggregation, `dataset.column_map`, LR warmup, optimizer hook, LR scheduler hook, and optional `ClipClampLogitScaleHook`.
- Use flattened values for nested optimizer/hook settings.
- Only enable fp16/distributed hooks when CUDA and dependencies are confirmed.

### Image classification pattern

- Extend `TrainingArgs` with multi-node config mappings such as `num_classes` mapped into both model head and augmentation nodes.
- Use tuple/list-like values for top-k metrics.
- Detect distributed launch variables before setting `launcher='pytorch'`.

These patterns are recipes, not full domain verification. For each real task, check the task-specific model, dataset schema, optional extras, and hardware.

## `modelscope.tools.train` and `modelscope.tools.eval`

The train tool parser expects:

```bash
python -m modelscope.tools.train CONFIG_PATH TRAINER_NAME
```

It constructs `kwargs = dict(cfg_file=CONFIG_PATH)`, calls `build_trainer(TRAINER_NAME, kwargs)`, then `trainer.train()`.

The eval tool parser expects:

```bash
python -m modelscope.tools.eval CONFIG_PATH --trainer_name TRAINER_NAME --checkpoint_path CHECKPOINT_PATH
```

It constructs `kwargs = dict(cfg_file=CONFIG_PATH)`, calls `build_trainer(TRAINER_NAME, kwargs)`, then `trainer.evaluate(CHECKPOINT_PATH)`.

Caveats:

- These are not dry-run commands.
- They do not validate model cache, dataset availability, credentials, CUDA, or write permissions before entering trainer construction.
- Use the safe preview helper and checklist first.

## Hooks, checkpointing, and logging overview

- Default config merging adds `CheckpointHook(interval=1)`, `TextLoggerHook(interval=10)`, and `IterTimerHook` when absent.
- `EvaluationHook` can be created from `evaluation.period` with `eval_strategy` as `by_epoch`, `by_step`, or `no` and a positive interval.
- `CheckpointHook` supports `save_strategy` (`by_epoch`, `by_step`, `no`), `interval`, `save_last`, `max_checkpoint_num`, and optional Hub push fields.
- `BestCkptSaverHook` follows evaluation cadence, compares `metric_key` with rule `max`/`min`, and can keep a limited number of best checkpoints.
- `LoadCheckpointHook` is injected by train/evaluate calls that receive a checkpoint path.
- `OptimizerHook` controls gradient accumulation through `cumulative_iters`, gradient clipping, and loss keys. Torch AMP/Apex hooks replace the optimizer processor and need compatible CUDA/AMP stacks.
- DDP/DeepSpeed/Megatron hooks alter device placement, process groups, checkpoint processors, and launch requirements; do not treat CPU import success as proof that these work.

## Evaluation-only flow

If the user wants to evaluate a checkpoint:

1. Confirm checkpoint file or directory format and whether it was created by the same trainer/checkpoint processor.
2. Confirm eval dataset and metrics are configured.
3. Confirm model/config revision and trust settings match the checkpoint.
4. Use API or tool shape only after preflight:

```python
trainer = build_trainer(name="trainer", default_args={"cfg_file": "config.yaml"})
metrics = trainer.evaluate(checkpoint_path="path/to/checkpoint.pth")
```

Outputs depend on trainer and metric configuration. Some prediction-saving flows require a user-supplied `saving_fn` and may write one file per process in distributed evaluation.

## Handoff after training

After a real training job finishes, route according to the next user intent:

- Inference with the resulting checkpoint or `output/` directory: `../pipelines-and-models/SKILL.md`.
- Upload/cache/model repository management: `../hub-and-cli/SKILL.md`.
- Serving/export/checkpoint conversion: `../serving-export-and-tools/SKILL.md`.
- Debugging failed training or evaluation: `references/troubleshooting.md`.
