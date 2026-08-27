# TrainingArgs Reference

## Purpose

Use this reference when converting ModelScope training CLI flags into a config, when extending `TrainingArgs` for a recipe, or when explaining how optimizer, LR scheduler, checkpoint, dataset, and model flags map into ModelScope config nodes.

The safe bundled helper `../scripts/build_training_args_preview.py` mirrors the verified package behavior for the base `TrainingArgs` dataclass without importing ModelScope or launching training.

## Verified API facts

- `build_trainer(name='trainer', default_args=None)` constructs a trainer from the ModelScope trainer registry. The default trainer name is `trainer`.
- `TrainingArgs.parse_cli(parser_args=None)` parses CLI-style arguments into a `TrainingArgs` object and stores unrecognized `--key value` pairs as extra config entries.
- `TrainingArgs.to_config(ignore_default_config=None)` returns `(cfg, args_dict)`, where `cfg` contains values mapped by field metadata `cfg_node`, and `args_dict` contains non-config fields such as dataset/model identifiers and control flags.
- If `ignore_default_config` is `None`, `to_config` uses `self.use_model_config`. When defaults are not ignored, every mapped field appears in the generated config; when defaults are ignored, only manually supplied fields should be merged over a model config.
- `optimizer_params` and `lr_scheduler_params` are comma-separated flattened `key=value` strings whose values are parsed into bool, int, float, `None`, or string.

## Base TrainingArgs families

`TrainingArgs` combines three dataclass families:

| Family | Typical fields | Runtime role |
| --- | --- | --- |
| Dataset args | `train_dataset_name`, `val_dataset_name`, `train_subset_name`, `val_subset_name`, `train_split`, `val_split`, namespaces, `dataset_json_file` | Select ModelScope or local dataset inputs and complex dataset mapping recipes. Dataset loading itself belongs in the dataset/config sub-skill. |
| Model args | `task`, `model`, `model_revision`, `model_type` | Identify the task, model id/local model directory, revision, and model type when not loading from an existing model config. |
| Train args | `seed`, dataloader batch/workers/shuffle/drop_last, `max_epochs`, `work_dir`, optimizer/LR scheduler, evaluation, checkpoint, Hub push flags | Populate `train.*` and `evaluation.*` config nodes used by `EpochBasedTrainer` and hooks. |

`use_model_config` is an additional control field. When true, recipes usually merge the generated config over the pretrained model configuration instead of replacing the config entirely.

## Common field-to-config mappings

This table covers the high-frequency base fields. Recipe-specific subclasses can add more fields with their own `cfg_node` metadata.

| CLI/field | Config node(s) | Notes |
| --- | --- | --- |
| `--task` | `task` | Task code used by model/pipeline/trainer logic. |
| `--model_type` | `model.type` | Required when no model config supplies model type. |
| `--per_device_train_batch_size` | `train.dataloader.batch_size_per_gpu` | Per-GPU/per-process batch size in distributed runs. |
| `--train_data_worker` | `train.dataloader.workers_per_gpu` | Keep low for debugging; increase only after data loading is stable. |
| `--train_shuffle` | `train.dataloader.shuffle` | Parsed as bool-like value by the CLI parser. |
| `--train_drop_last` | `train.dataloader.drop_last` | Often needed for distributed or fixed-shape training. |
| `--per_device_eval_batch_size` | `evaluation.dataloader.batch_size_per_gpu` | Evaluation batch size. |
| `--eval_data_worker` | `evaluation.dataloader.workers_per_gpu` | Evaluation data workers. |
| `--eval_shuffle` | `evaluation.dataloader.shuffle` | Usually false for evaluation. |
| `--eval_drop_last` | `evaluation.dataloader.drop_last` | Usually false unless metric logic requires equal batches. |
| `--max_epochs` | `train.max_epochs` | Required by the default trainer if not otherwise configured. |
| `--work_dir` | `train.work_dir` | Trainer writes logs/checkpoints here during real jobs. Preview helper does not create it. |
| `--lr` | `train.optimizer.lr` | Base learning rate. |
| `--optimizer` | `train.optimizer.type` | PyTorch/native or registered optimizer name; examples use `AdamW`, `SGD`. |
| `--optimizer_params` | `train.optimizer.*` | Flattened extra optimizer settings such as weight decay or epsilon. |
| `--lr_scheduler` | `train.lr_scheduler.type` | Examples use `LinearLR`, `StepLR`, `LambdaLR`, or task-specific aliases after recipe conversion. |
| `--lr_scheduler_params` | `train.lr_scheduler.*` | Flattened scheduler extras. |
| `--lr_strategy` | `train.lr_scheduler.options.lr_strategy` | One of `by_epoch`, `by_step`, `no`. |
| `--logging_interval` | `train.logging.interval` | Used to form a text logger hook through default config conversion. |
| `--eval_strategy` | `evaluation.period.eval_strategy` | One of `by_epoch`, `by_step`, `no`. |
| `--eval_interval` | `evaluation.period.interval` | Positive interval for evaluation hook when evaluation is enabled. |
| `--eval_metrics` | `evaluation.metrics` | Metric name or config. Metrics are required when an eval dataset exists and no task default metric applies. |
| `--save_strategy` | `train.checkpoint.period.save_strategy` | One of `by_epoch`, `by_step`, `no`. |
| `--save_interval` | `train.checkpoint.period.interval` | Checkpoint interval. |
| `--max_checkpoint_num` | `train.checkpoint.period.max_checkpoint_num` | Older checkpoints may be deleted when this limit is exceeded. |
| `--save_best_checkpoint` | `train.checkpoint.best.save_best` | Best-checkpoint saving depends on evaluation results. |
| `--metric_for_best_model` | `train.checkpoint.best.metric_key` | Must match a metric key in `trainer.metric_values`. |
| `--metric_rule_for_best_model` | `train.checkpoint.best.rule` | `max` or `min`. |
| `--push_to_hub` and related Hub fields | `train.checkpoint.period.*` Hub fields | Real jobs may upload checkpoints; requires token/credentials and should be explicitly authorized. |
| `--push_to_hub_best` and related best Hub fields | `train.checkpoint.best.*` Hub fields | Same credential and side-effect caveats as periodic checkpoint upload. |

## Flattened value syntax

`optimizer_params` and `lr_scheduler_params` accept comma-separated pairs:

```bash
--optimizer_params 'weight_decay=0.8,eps=1e-6,correct_bias=False'
--lr_scheduler_params 'initial_lr=3e-5,niter_decay=1'
```

The verified unit test confirms this becomes:

```text
train.optimizer.weight_decay = 0.8
train.optimizer.eps = 1e-6
train.optimizer.correct_bias = false
train.lr_scheduler.initial_lr = 3e-5
train.lr_scheduler.niter_decay = 1
```

Caveats:

- The parser splits pairs on commas and then on `=`. Do not include unescaped commas inside a value.
- Use `True`/`False`, `true`/`false`, `None`, `none`, or `null` for booleans/nulls.
- Quote shell values to prevent the shell from interpreting parentheses, commas, or spaces.
- Unknown CLI pairs are treated as config overrides by stripping hyphens from the key in the current implementation. Prefer known fields or explicit recipe subclass fields for important settings.

## Dataset column mapping patterns

Training examples commonly map raw dataset columns to preprocessor/model keys before training:

- The README example loads a poetry dataset and remaps `text1` to `src_txt` before passing datasets to a GPT-style trainer.
- Text classification examples add fields such as `first_sequence`, `second_sequence`, `label`, `labels`, and `preprocessor` with `cfg_node` metadata under `preprocessor.*`.
- Token classification examples add sequence and label fields, derive label ids from training/eval data, and set `evaluation.metrics` to a task-specific metric config.
- Multi-modal embedding examples add a `dataset_column_map` field that maps into `dataset.column_map` through the same flattened `key=value` mechanism.
- `dataset_json_file` supports complex multi-dataset recipes. The source function expects a list of entries with a `dataset` load-argument object, `column_mapping`, and `usage` value (`train`, `val`, or a float split ratio). In the current docstring the field is also described as `split`; check the recipe and validate before a real job.

Always verify expected columns before constructing the trainer. If the user only needs dataset loading or a local recipe validator, route to `../datasets-config/SKILL.md`.

## Extending TrainingArgs in a recipe

Recipe examples define a subclass with `@dataclass(init=False)` and fields whose metadata contains at least `help`, and optionally `cfg_node`, `choices`, or `cfg_setter`.

```python
from dataclasses import dataclass, field
from modelscope import TrainingArgs

@dataclass(init=False)
class MyTaskArgs(TrainingArgs):
    first_sequence: str = field(
        default=None,
        metadata={
            'help': 'Dataset text column used by the preprocessor',
            'cfg_node': 'preprocessor.first_sequence',
        })
```

Typical recipe flow:

1. Parse flags: `training_args = MyTaskArgs().parse_cli()`.
2. Convert to config: `config, args = training_args.to_config()`.
3. Load/remap datasets from `args.*`.
4. Define `cfg_modify_fn(cfg)` to either merge over model config when `args.use_model_config` is true or replace with the generated config.
5. Pass `model`, datasets, seed/work_dir, and `cfg_modify_fn` through `default_args` to `build_trainer`.

## Safe preview examples

Preview a short text-classification-style config without creating files:

```bash
python scripts/build_training_args_preview.py \
  --task text-classification \
  --model damo/example-model \
  --train_dataset_name clue \
  --train_subset_name tnews \
  --train_split train \
  --val_dataset_name clue \
  --val_subset_name tnews \
  --val_split validation \
  --max_epochs 1 \
  --per_device_train_batch_size 16 \
  --per_device_eval_batch_size 16 \
  --eval_strategy by_step \
  --eval_interval 100 \
  --optimizer AdamW \
  --lr 1e-5 \
  --optimizer_params weight_decay=0.01,eps=1e-8 \
  --format summary
```

Preview JSON for automation:

```bash
python scripts/build_training_args_preview.py \
  --max_epochs 2 \
  --save_strategy by_epoch \
  --save_interval 1 \
  --max_checkpoint_num 2 \
  --format json
```

The helper intentionally does not validate that a model id, dataset id, metric, optimizer, or scheduler exists. It is a config preview and preflight aid, not a training verifier.
