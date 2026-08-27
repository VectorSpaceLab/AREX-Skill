# DINO training workflows

This reference turns the repository launchers into reviewed command shapes.
Replace illustrative `/data/...` and `runs/...` values with local paths. The
commands assume the checkout root is the current directory and that the setup
gate in [data-model-setup](../../data-model-setup/SKILL.md) passed. They are
examples to review, not commands that this skill runs.

## Choose the configuration and launch

| Goal | Config | Shipped defaults | Recommended first mode |
|---|---|---|---|
| ResNet-50 baseline, four feature levels | `config/DINO/DINO_4scale.py` | `return_interm_indices=[1,2,3]`, `num_feature_levels=4`, `batch_size=2`, 12 epochs, LR drop at 11 | single process for a smoke; multi-GPU for the reference batch |
| ResNet-50, five feature levels | `config/DINO/DINO_5scale.py` | `return_interm_indices=[0,1,2,3]`, `num_feature_levels=5`, `batch_size=1` | multi-GPU; it is more memory intensive |
| Swin-L 384, four feature levels | `config/DINO/DINO_4scale_swin.py` | Swin-L `swin_L_384_22k`, `use_checkpoint=True`, `batch_size=2` | one process or distributed after a local backbone checkpoint is present |
| ConvNeXt-XL, four feature levels | `config/DINO/DINO_4scale_convnext.py` | ConvNeXt `convnext_xlarge_22k`, `batch_size=2` | one process or distributed after a local backbone checkpoint is present |

The shipped Swin and ConvNeXt paths expect `backbone_dir` and local pretrained
backbone files. Do not turn a missing asset into an implicit network download.
The supported backbone names and exact feature-index constraints are in
[configuration.md](configuration.md).

## Safe command planning

The bundled planner statically validates the config and prints a command. It
never starts a process, downloads a checkpoint, or creates a dataset:

```bash
python skills/disco/dino/sub-skills/training/scripts/build_dino_command.py --help
python skills/disco/dino/sub-skills/training/scripts/build_dino_command.py \
  --repo-root . \
  --config config/DINO/DINO_4scale.py \
  --coco-path /data/COCO \
  --output-dir runs/dino-r50-ms4 \
  --mode single
```

For command planning before data has been mounted, add the explicit
`--allow-missing-data` flag and treat the result as unlaunchable until the
setup gate passes. For a custom COCO-style dataset, make class semantics
explicit:

```bash
python skills/disco/dino/sub-skills/training/scripts/build_dino_command.py \
  --repo-root . --config config/DINO/DINO_4scale.py \
  --coco-path /data/custom-coco --custom-dataset \
  --num-classes 5 --dn-labelbook-size 6 \
  --output-dir runs/custom-ms4 --mode single
```

Here `5` means the maximum category ID plus one, not five arbitrary names;
the conservative custom-data rule requires a labelbook of at least 6. The
planner appends these as `--options num_classes=5 dn_labelbook_size=6` after
all direct parser arguments. It rejects an ambiguous custom class count.

## Single-process training

The repository's single-process launcher is equivalent to:

```bash
python main.py \
  --output_dir runs/dino-r50-ms4 \
  -c config/DINO/DINO_4scale.py \
  --coco_path /data/COCO
```

For mixed precision, append `--amp`. To make a bounded configuration change,
append options **at the end** (the repository `DictAction` consumes all
following `KEY=VALUE` tokens):

```bash
python main.py \
  --output_dir runs/dino-r50-ms4-amp \
  -c config/DINO/DINO_4scale.py \
  --coco_path /data/COCO --amp \
  --options batch_size=1 use_ema=False
```

Use one visible GPU through the environment or the machine's scheduler, and
keep `batch_size` as a per-process value. A plain `python main.py` does not
initialize distributed mode; it uses a random training sampler and a
sequential validation sampler.

## Multi-GPU on one or more nodes

The checked-in launcher uses the older module name; the following modern
`torch.distributed.run` spelling supplies the same `WORLD_SIZE`, `LOCAL_RANK`,
and rank environment consumed by `util/misc.py`:

```bash
python -m torch.distributed.run \
  --nproc_per_node=8 \
  main.py --output_dir runs/dino-r50-ms4-8gpu \
  -c config/DINO/DINO_4scale.py --coco_path /data/COCO
```

The repository-equivalent legacy form is:

```bash
python -m torch.distributed.launch --nproc_per_node=8 main.py \
  --output_dir runs/dino-r50-ms4-8gpu \
  -c config/DINO/DINO_4scale.py --coco_path /data/COCO
```

Prefer `torch.distributed.run` on a current PyTorch installation. DINO's
initializer sets the NCCL backend and selects each process's local CUDA
ordinal, so a CPU-only distributed run is not a supported fallback.

For a two-node, eight-GPU-per-node plan, run the corresponding command on
both nodes, changing `--node_rank` from 0 to 1 and using a reachable address
for rank 0:

```bash
python -m torch.distributed.run \
  --nnodes=2 --nproc_per_node=8 --node_rank=0 \
  --master_addr=TRAIN_NODE_0 --master_port=29500 \
  main.py --output_dir runs/dino-r50-ms5-16gpu \
  -c config/DINO/DINO_5scale.py --coco_path /data/COCO
```

The planner requires `--master-addr` for a multi-node command and prints the
per-node rank. Do not start two ranks with the same rank or point unrelated
jobs at the same output directory.

## Submitit / Slurm

Submitit is a scheduler adapter, not a local multi-process substitute. The
repository wrapper requires a non-empty `--job_dir`, asks Slurm for
`--ngpus` GPUs per node and `--nodes` nodes, and derives the distributed rank
from the Submitit job environment. A reviewed one-node example is:

```bash
python run_with_submitit.py \
  --timeout 3000 --job_name DINO \
  --job_dir runs/submitit/dino-r50-ms4-%j \
  --ngpus 8 --nodes 1 \
  -c config/DINO/DINO_4scale.py --coco_path /data/COCO
```

The corresponding five-scale reference shape requests two nodes in the
original launcher because its default is one image per GPU:

```bash
python run_with_submitit.py \
  --timeout 3000 --job_name DINO \
  --job_dir runs/submitit/dino-r50-ms5-%j \
  --ngpus 8 --nodes 2 \
  -c config/DINO/DINO_5scale.py --coco_path /data/COCO
```

For Swin or ConvNeXt, add the config's required local asset directory as a
config option:

```bash
python run_with_submitit.py \
  --timeout 3000 --job_name DINO \
  --job_dir runs/submitit/dino-swin-%j --ngpus 8 --nodes 1 \
  -c config/DINO/DINO_4scale_swin.py --coco_path /data/COCO \
  --options backbone_dir=/data/backbones
```

The current wrapper's `--cpus_per_task` parser argument is not honored when
it calls `update_parameters`: the executor currently submits a hard-coded
16 CPUs per task. The planner warns if a different value is requested. The
wrapper also relies on a site-specific shared-folder arrangement for its
initialization URI. Neither that arrangement nor an active Slurm service was
available in the verified environment; inspect the cluster policy before
submitting. Never treat a successful local `submitit` import as a submitted
job.

## Batch size, schedule, and memory

`batch_size` is the `BatchSampler` size on each process. Compute:

```text
world_size = nodes * GPUs per node
 effective global batch = config batch_size * world_size
```

The shipped 4-scale configuration uses `2 * 8 = 16` for the original
8-GPU reference. The shipped 5-scale configuration uses `1 * 16 = 16` for
the original two-node reference. A one-node 5-scale run with eight GPUs has
a global batch of 8, not 16. Learning rates are not automatically rescaled;
record any deliberate change and do not compare it as the same recipe.

On an out-of-memory failure, lower the per-process `batch_size` first, try
`--amp`, or use 4-scale instead of 5-scale. Swin's `use_checkpoint=True` is
already enabled in its shipped config. Gradient accumulation is not
implemented by `main.py`; do not claim an equivalent global batch by merely
adding an unsupported flag. Reduce `num_queries` or image augmentation only
as an explicitly changed experiment.

The default scheduler is `StepLR(args.lr_drop)`. `onecyclelr=True` steps per
batch, while `multi_step_lr=True` uses `lr_drop_list`; these are config
choices, not launch flags. The default `save_checkpoint_interval=1` gives a
checkpoint every epoch in addition to the rolling checkpoint.

## Resume, pretrain, and fine-tune

### Full resume

Use a matching full training checkpoint:

```bash
python main.py \
  --output_dir runs/dino-r50-ms4 \
  -c config/DINO/DINO_4scale.py --coco_path /data/COCO \
  --resume runs/dino-r50-ms4/checkpoint.pth
```

`main.py` loads `checkpoint['model']` strictly. For training (not `--eval`),
it restores `optimizer`, `lr_scheduler`, and `start_epoch` when all three
checkpoint fields exist. An HTTPS `--resume` is accepted by `main.py`, but this
skill does not download it and the planner passes HTTPS URLs through unchanged;
non-HTTPS resume values are resolved as local paths under the repository root.

Before interpreting an explicit `--resume`, check whether the selected
output directory already contains `checkpoint.pth`: the code overwrites the
argument with that path automatically. To restart a different experiment,
choose a new output directory or move the old rolling checkpoint after
preserving it.

### Pretrained initialization and fine-tuning

Use a new output directory and a local model checkpoint when changing class
heads or adapting a compatible architecture:

```bash
python main.py \
  --output_dir runs/custom-ms4 \
  -c config/DINO/DINO_4scale.py --coco_path /data/custom-coco \
  --pretrain_model_path /data/checkpoints/dino-r50.pth \
  --finetune_ignore label_enc.weight class_embed \
  --options num_classes=5 dn_labelbook_size=6
```

This path extracts `checkpoint['model']`, cleans state-dict prefixes, filters
keys containing any ignore substring, and calls `load_state_dict(...,
strict=False)`. It does not restore optimizer state, scheduler state, or the
starting epoch. A model/scale/backbone mismatch will still leave missing or
unexpected keys; inspect the logged load result instead of assuming transfer
was complete. `--resume` and `--pretrain_model_path` are mutually exclusive
in the planner because `main.py` gives resume precedence.

## Artifacts and safe stopping

At startup rank 0 saves the merged `config_cfg.py`, raw parser arguments in
`config_args_raw.json`, and later the combined arguments in
`config_args_all.json`; `info.txt` records the command and ranks. During
training, expect:

- `checkpoint.pth`: rolling full state, overwritten after each epoch;
- `checkpoint####.pth`: extra full states at each `save_checkpoint_interval`
  or LR-drop boundary, with the filename's four digits based on the
  zero-based epoch;
- `checkpoint_best_regular.pth` and, if EMA is enabled,
  `checkpoint_best_ema.pth`;
- `log.txt`: JSON lines combining train stats, validation stats, best metrics,
  epoch, and elapsed time;
- `eval/`: saved evaluator state for training-time validation; and
  `eval.pth` for an explicit `--eval` run;
- `results-<rank>.pkl` only when `--save_results` is used.

Training performs validation after every epoch. Route metric interpretation or
standalone evaluation to [inference-evaluation](../../inference-evaluation/SKILL.md).

For an interactive job, prefer stopping after the current epoch so the rolling
checkpoint is complete. If interrupted mid-epoch, the last checkpoint may be
from the previous epoch; rerun the same command and inspect the restored epoch
in `log.txt`. For a scheduler preemption, Submitit's `checkpoint()` callback
points `args.resume` at `checkpoint.pth` when it exists, enabling a requeued
job to continue. Do not delete a partial output directory, launch a second
job into it, or assume a termination signal has flushed a mid-epoch state.
Record whether stopping was clean, preempted, or killed.

## Legacy launcher note

The checked-in shell launchers append `dn_scalar`, `dn_label_coef`, and
`dn_bbox_coef`. The current config/model sources use `dn_number`,
`dn_box_noise_scale`, `dn_label_noise_ratio`, and the loss-coefficient names
in the configuration; no current source reads those three launcher keys. The
planner therefore emits a minimal command and warns if a caller explicitly
requests one of the legacy keys.
