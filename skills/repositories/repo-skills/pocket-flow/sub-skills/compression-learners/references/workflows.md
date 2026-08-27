# Compression Learner Workflows

PocketFlow learner workflows are TensorFlow 1.x training/evaluation jobs. The command examples below are command patterns for an active PocketFlow checkout; this skill does not run them. First handle environment, `path.conf`, local/docker/seven launcher semantics, data paths, model URLs, and GPU discovery through [execution-config](../../execution-config/SKILL.md).

For safe previews, use the bundled helper from the `compression-learners` sub-skill root:

```bash
python scripts/build_learner_command.py --learner full-prec --mode local \
  --run-script nets/resnet_at_cifar10_run.py
```

From this reference directory, the same helper is [`../scripts/build_learner_command.py`](../scripts/build_learner_command.py). It validates the learner id and prints an abstract official-launcher or direct-Python command; it never starts training.

## Baseline first

Always establish a full-precision baseline or a known pretrained checkpoint before comparing compression results.

Preview a local full-precision training command:

```bash
python scripts/build_learner_command.py --mode local \
  --run-script nets/resnet_at_cifar10_run.py \
  --learner full-prec -- --resnet_size 20
```

Official command pattern after setup:

```bash
./scripts/run_local.sh nets/resnet_at_cifar10_run.py \
  --learner full-prec --resnet_size 20
```

Use `--exec_mode eval` in a direct-Python pattern when the task is evaluation only and a checkpoint exists. Model/data-specific flags such as `--resnet_size`, `--nb_epochs_rat`, dataset paths, and sample counts are owned by the run script and `ModelHelper`; route authoring questions to [custom-models-data](../../custom-models-data/SKILL.md).

## Distillation overlay

Distillation is an overlay on full-precision or compression learners, not a separate learner id.

Common flags:

```text
--enbl_dst --loss_w_dst 4.0 --tempr_dst 4.0
```

Pattern:

```bash
python scripts/build_learner_command.py --mode local \
  --run-script nets/resnet_at_cifar10_run.py \
  --learner weight-sparse -- \
  --enbl_dst --loss_w_dst 4.0 --tempr_dst 4.0 \
  --ws_prune_ratio 0.75 --ws_prune_ratio_prtl uniform
```

Distillation internally prepares a teacher full-precision model under a separate scope. Make sure the teacher/full checkpoint is available and that `--save_path_dst`/`--save_path` conventions do not collide with the learner's compressed-model output paths.

## Channel pruning variants

### Original channel pruning: `channel`

Use this when the task needs the original channel pruning behavior, LASSO feature reconstruction, `cp_prune_option`, RL auto preserve-ratio search, group fine-tuning, or list preserve ratios.

Uniform preserve ratio:

```bash
python scripts/build_learner_command.py --mode local \
  --run-script nets/resnet_at_cifar10_run.py \
  --learner channel -- \
  --cp_prune_option uniform --cp_uniform_preserve_ratio 0.5
```

Layer/list preserve ratios:

```bash
python scripts/build_learner_command.py --mode local \
  --run-script nets/resnet_at_cifar10_run.py \
  --learner channel -- \
  --cp_prune_option list --cp_prune_list_file ratio.list
```

RL-auto preserve ratio:

```bash
python scripts/build_learner_command.py --mode local \
  --run-script nets/resnet_at_cifar10_run.py \
  --learner channel -- \
  --cp_prune_option auto --cp_preserve_ratio 0.5 \
  --cp_nb_rlouts 200 --cp_nb_rlouts_min 50
```

Useful refinements:

- `--cp_finetune=True` enables group fine-tuning between groups.
- `--cp_retrain=True` uses retraining rather than short fine-tuning between groups.
- `--cp_list_group` controls group size; small groups are slower but may recover accuracy better.
- `--cp_quadruple=True` can constrain channel counts toward multiples useful for mobile inference.

### Remastered channel pruning: `chn-pruned-rmt`

Use this for the remastered LASSO/least-square channel pruning implementation with clearer skip and warm-start controls. It does not provide the original learner's RL auto search.

```bash
python scripts/build_learner_command.py --mode local \
  --run-script nets/resnet_at_cifar10_run.py \
  --learner chn-pruned-rmt -- \
  --cpr_prune_ratio 0.50 --cpr_skip_frst_layer=True \
  --cpr_skip_last_layer=False
```

Skip specific operations with `--cpr_skip_op_names conv_a,conv_b`; warm-start a previously channel-pruned model with `--cpr_warm_start=True --cpr_save_path_ws <checkpoint-prefix>`.

### GPU-based channel pruning: `chn-pruned-gpu`

Use this only when the task explicitly wants the GPU-oriented `cpg_*` implementation.

```bash
python scripts/build_learner_command.py --mode local \
  --run-script nets/resnet_at_cifar10_run.py \
  --learner chn-pruned-gpu -- \
  --cpg_prune_ratio_type uniform --cpg_prune_ratio 0.5 \
  --cpg_skip_ht_layers=True
```

For a ratio file, change `--cpg_prune_ratio_type list` and set `--cpg_prune_ratio_file`.

### Discrimination-aware channel pruning: `dis-chn-pruned`

Use this for DCP staged pruning with discrimination-aware losses and layer/block fine-tuning.

```bash
python scripts/build_learner_command.py --mode local \
  --run-script nets/resnet_at_cifar10_run.py \
  --learner dis-chn-pruned -- \
  --dcp_prune_ratio 0.75 --dcp_nb_stages 3
```

`--dcp_nb_stages`, `--dcp_nb_iters_block`, and `--dcp_nb_iters_layer` trade accuracy recovery against runtime. Distillation can be combined with `--enbl_dst`.

## Weight sparsification: `weight-sparse`

Use this to impose dynamic masks on weights. It reduces non-zero parameter count; actual inference speedup depends on sparse-operation support.

Uniform sparsity:

```bash
python scripts/build_learner_command.py --mode local \
  --run-script nets/resnet_at_cifar10_run.py \
  --learner weight-sparse -- \
  --ws_prune_ratio 0.75 --ws_prune_ratio_prtl uniform
```

Heuristic layer-wise sparsity:

```bash
python scripts/build_learner_command.py --mode local \
  --run-script nets/resnet_at_cifar10_run.py \
  --learner weight-sparse -- \
  --ws_prune_ratio 0.75 --ws_prune_ratio_prtl heurist
```

RL-optimized sparsity:

```bash
python scripts/build_learner_command.py --mode local \
  --run-script nets/resnet_at_cifar10_run.py \
  --learner weight-sparse -- \
  --ws_prune_ratio 0.75 --ws_prune_ratio_prtl optimal \
  --ws_nb_rlouts 200 --ws_nb_rlouts_min 50
```

Schedule controls:

- `--ws_iter_ratio_beg` and `--ws_iter_ratio_end` define the training fraction over which sparsity ramps up.
- `--ws_prune_ratio_exp` changes the shape of the dynamic schedule.
- `--ws_mask_update_step` controls how often masks are recomputed. This is the learner-defined flag name.

## Uniform quantization: `uniform`

Use this for PocketFlow's self-developed uniform quantizer with optional activation quantization, bucketing, and RL bit allocation.

Basic fixed-bit quantization:

```bash
python scripts/build_learner_command.py --mode local \
  --run-script nets/resnet_at_cifar10_run.py \
  --learner uniform -- \
  --uql_weight_bits 4 --uql_activation_bits 4
```

Bucketing:

```bash
python scripts/build_learner_command.py --mode local \
  --run-script nets/resnet_at_cifar10_run.py \
  --learner uniform -- \
  --uql_weight_bits 8 --uql_activation_bits 8 \
  --uql_use_buckets=True --uql_bucket_type channel
```

RL bit allocation:

```bash
python scripts/build_learner_command.py --mode local \
  --run-script nets/mobilenet_at_ilsvrc12_run.py \
  --learner uniform -- \
  --uql_enbl_rl_agent=True --uql_equivalent_bits 4 \
  --uql_w_bit_min 2 --uql_w_bit_max 8
```

Use the source-defined flag `--uql_quant_epochs` to control quantization fine-tuning epochs.

## TensorFlow quantization-aware training: `uniform-tf`

Use this when the downstream goal is TensorFlow 1.x quantization-aware training and likely TFLite export.

```bash
python scripts/build_learner_command.py --mode local \
  --run-script nets/resnet_at_cifar10_run.py \
  --learner uniform-tf -- \
  --uqtf_weight_bits 8 --uqtf_activation_bits 8 \
  --uqtf_quant_delay 0 --nb_epochs_rat 0.2
```

Manual insertion mode is available with `--uqtf_enbl_manual_quant=True`, but it should be treated as advanced because it inspects activation nodes. After a `uniform-tf` checkpoint is produced, route PB/TFLite export to [deployment-conversion](../../deployment-conversion/SKILL.md); do not treat conversion as part of the learner run.

## Non-uniform quantization: `non-uniform`

Use this to optimize non-uniform reconstruction levels/cluster centers. It usually targets compression and accuracy recovery rather than direct integer-runtime acceleration.

```bash
python scripts/build_learner_command.py --mode local \
  --run-script nets/resnet_at_cifar10_run.py \
  --learner non-uniform -- \
  --nuql_weight_bits 4 --nuql_activation_bits 32 \
  --nuql_init_style quantile --nuql_opt_mode weights
```

Bucketing and RL search mirror the uniform learner with `nuql_` prefixes:

```bash
python scripts/build_learner_command.py --mode local \
  --run-script nets/mobilenet_at_ilsvrc12_run.py \
  --learner non-uniform -- \
  --nuql_enbl_rl_agent=True --nuql_equivalent_bits 4 \
  --nuql_use_buckets=True --nuql_bucket_type channel
```

Use the source-defined flag `--nuql_quant_epochs` to control quantization fine-tuning epochs.

## Launcher mode choice

The helper supports `--mode local`, `--mode docker`, `--mode seven`, and `--mode direct`:

- `local` previews the official `scripts/run_local.sh` pattern. The official source launcher selects GPUs, rewrites `main.py`, and recreates `logs`; use `execution-config` before running it.
- `docker` previews the official `scripts/run_docker.sh` pattern. It requires Docker/NVIDIA Docker and is not validated by this sub-skill.
- `seven` previews the official `scripts/run_seven.sh` pattern. It is Tencent Seven-cluster specific and should usually remain reference-only.
- `direct` prints `python <run_script> --exec_mode=<train|eval> --learner=<id> ...`. Direct mode bypasses `path.conf` argument injection, so provide all required data/model path flags explicitly or use `execution-config` to generate them.

## Verification and performance boundary

The generated skill verified learner ids, constructor mapping, source flags, and safe command generation. Full native training/performance claims from PocketFlow docs require real datasets, pretrained checkpoints, TF1 runtime readiness, and often GPU/multi-GPU hardware. Treat those runs as long-running and not skill-verified.
