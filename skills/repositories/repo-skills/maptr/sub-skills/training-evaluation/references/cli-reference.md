# CLI Reference

All options below are taken from the repository's `tools/train.py`,
`tools/test.py`, and the two MapTR distributed shell contracts. Use
`python tools/train.py --help` and `python tools/test.py --help` as the final
syntax authority for this pinned revision.

## Launcher Matrix

| Goal | Entry point | Required launch mode | Metric behavior |
|---|---|---|---|
| Single-process training | `tools/train.py` | `--launcher none` | Training-time validation follows config unless `--no-validate` |
| Distributed training | `tools/dist_train.sh` or equivalent validator | `torch.distributed.launch`, `--launcher pytorch` | Appends deterministic mode |
| MapTR evaluation | `tools/dist_test_map.sh` or equivalent validator | `torch.distributed.launch`, `--launcher pytorch` | Appends `--eval chamfer` |
| Generic test wrapper | `tools/dist_test.sh` | Distributed | Appends `--eval bbox`; do not use for MapTR vector metrics |

The checked-in `tools/test.py` has an assertion in its non-distributed branch,
so a direct `tools/test.py ... --launcher none` is not a supported evaluation
route even with one GPU. Use the distributed form with `--gpus 1`.

## `tools/train.py`

Synopsis:

```text
python tools/train.py CONFIG [options]
```

### Positional

- `CONFIG`: config file path. MapTR configs inherit base files and commonly
  enable `plugin=True` with `plugin_dir='projects/mmdet3d_plugin/'`.

### Training options

| Option | Meaning and cautions |
|---|---|
| `--work-dir DIR` | Directory for logs, dumped merged config, and checkpoints. CLI wins over config; otherwise default is `./work_dirs/<config stem>`. Use a unique, writable path. |
| `--resume-from FILE` | Requests runner resume, but the script only assigns it when `FILE` is an existing regular file. Validate it yourself. |
| `--no-validate` | Skip validation during training. It does not skip model/data initialization or checkpoint writes. |
| `--gpus N` | GPU count for the non-distributed path only. It does not invoke distributed training. |
| `--gpu-ids ID [ID ...]` | Explicit GPU ids for non-distributed training only; mutually exclusive with `--gpus`. |
| `--seed INT` | Random seed; default `0`. The script records it in config metadata and calls the mmdet seed helper. |
| `--deterministic` | Enables deterministic cuDNN options through the seed helper. The distributed wrapper always appends this. It is not a cross-machine bitwise guarantee. |
| `--options KEY=VALUE ...` | Deprecated alias for `--cfg-options`; cannot be combined with it. |
| `--cfg-options KEY=VALUE ...` | Merge overrides into the loaded config. Quote list/tuple values and values containing shell metacharacters. |
| `--launcher {none,pytorch,slurm,mpi}` | Distributed initialization mode. `none` is the default; MapTR distributed wrappers use `pytorch`. |
| `--local_rank INT` | Local rank supplied by the launcher; normally set by the launcher/environment, default `0`. |
| `--autoscale-lr` | Multiplies configured learning rate by `len(cfg.gpu_ids)/8`; record this as a changed experiment setting. |

The parser rejects simultaneous `--options` and `--cfg-options`. The script
loads and merges the config before importing custom modules, then sets the
work directory and GPU ids, initializes distributed mode, dumps the merged
config, logs environment/model details, builds datasets/model, and enters the
custom training helper.

### Safe override examples

```bash
# Reduce loader workers only if the config accepts this override.
python tools/train.py CONFIG.py --gpus 1 \
  --cfg-options data.workers_per_gpu=1 \
  --work-dir work_dirs/low_worker_probe

# Explicitly disable in-training validation for an approved long run.
python tools/train.py CONFIG.py --gpus 1 --no-validate \
  --work-dir work_dirs/no_validation_run
```

Do not infer that a successful parser invocation proves a custom plugin import,
CUDA extension, dataset, checkpoint, or GPU memory plan.

## `tools/test.py`

Synopsis:

```text
python tools/test.py CONFIG CHECKPOINT [options]
```

| Option | Meaning and cautions |
|---|---|
| `--out FILE.pkl` | Parsed as a result output request, but the checked-in distributed path reaches an assertion instead of dumping outputs. Do not use as a promised artifact mechanism. |
| `--fuse-conv-bn` | Fuses convolution and batch-normalization layers; may slightly improve inference speed, but changes the execution graph. Use only when the backend and comparison plan allow it. |
| `--format-only` | Format results without dataset evaluation. It cannot be combined with `--eval`. |
| `--eval METRIC [METRIC ...]` | Dataset metrics. Map dataset evaluation supports `chamfer` and `iou`; project MapTR evaluation uses `chamfer`. Do not pass `bbox`. |
| `--show` | Requests showing results, but the distributed call does not pass this flag into `custom_multi_gpu_test` in this revision. Use a visualization workflow instead. |
| `--show-dir DIR` | Requests a show directory, subject to the same distributed-path limitation. Route to visualization if output is required. |
| `--gpu-collect` | Collect distributed result shards through GPU communication instead of a temporary directory. This consumes GPU memory and can fail under tight memory. |
| `--tmpdir DIR` | Temporary directory for distributed result collection when `--gpu-collect` is not used. Ensure it is writable and has enough space. |
| `--seed INT` | Seed for test-time setup; default `0`. Pair with `--deterministic` when comparing runs. |
| `--deterministic` | Enables deterministic cuDNN options. It does not remove backend/library nondeterminism. |
| `--cfg-options KEY=VALUE ...` | Merge config overrides before dataset/model construction. Ensure the checkpoint remains compatible. |
| `--options KEY=VALUE ...` | Deprecated alias for `--eval-options`; cannot be combined with it. |
| `--eval-options KEY=VALUE ...` | Keyword options forwarded to `dataset.evaluate()`, such as an approved `jsonfile_prefix`. Do not use it to bypass metric or path checks. |
| `--launcher {none,pytorch,slurm,mpi}` | Distributed initialization. The MapTR wrapper uses `pytorch`; the non-distributed execution branch is asserted out. |
| `--local_rank INT` | Launcher-provided local rank, default `0`. |

`tools/test.py` requires at least one of `--out`, `--eval`, `--format-only`,
`--show`, or `--show-dir`, rejects `--eval` with `--format-only`, and requires
`--out` to end in `.pkl` or `.pickle` before reaching the distributed path.
The MapTR wrapper's appended `--eval chamfer` satisfies the required
operation.

## Distributed Shell Contracts

### Training

```text
CONFIG=$1
GPUS=$2
PORT=${PORT:-28509}
python3 -m torch.distributed.launch \
  --nproc_per_node=$GPUS --master_port=$PORT \
  tools/train.py $CONFIG --launcher pytorch EXTRA_ARGS --deterministic
```

Arguments after the GPU count are passed to `tools/train.py` before the forced
`--deterministic`. Typical safe extras are `--work-dir`, `--resume-from`,
`--seed`, `--cfg-options`, `--no-validate`, and `--autoscale-lr`.

### MapTR evaluation

```text
CONFIG=$1
CHECKPOINT=$2
GPUS=$3
PORT=${PORT:-29503}
python3 -m torch.distributed.launch \
  --nproc_per_node=$GPUS --master_port=$PORT \
  tools/test.py $CONFIG $CHECKPOINT --launcher pytorch EXTRA_ARGS \
  --eval chamfer
```

The validator rejects attempts to add a competing `--eval` or a different
launcher, preserving the MapTR metric contract. A user may still pass other
recognized test options after `--`, but must account for their actual source
semantics, especially `--out`, `--show`, `--show-dir`, and collection mode.

## Config Fields That Affect Run Interpretation

The canonical tiny 24-epoch config contains the following important fields;
other configs may differ:

```text
plugin=True
plugin_dir='projects/mmdet3d_plugin/'
point_cloud_range=[-15,-30,-2,15,30,2]
map_classes=['divider','ped_crossing','boundary']
fixed_ptsnum_per_gt_line=20
fixed_ptsnum_per_pred_line=20
bev_h=200, bev_w=100
num_query=900, num_vec=50
queue_length=1
evaluation.interval=2, evaluation.metric='chamfer'
fp16.loss_scale=512
checkpoint_config.interval=1
runner.max_epochs=24
```

Treat this as a config-reading checklist, not a replacement for printing the
exact config used for a run.
