# PySOT training workflow

PySOT training is a distributed CUDA workflow. Safe local validation can check configs and paths, but a real run needs user-supplied datasets, pretrained backbone/model files, compatible PyTorch/CUDA, and enough GPUs/memory.

## Preconditions

Before constructing a training command, confirm:

- PySOT import style: run from the checkout with `PYTHONPATH` pointing at the checkout root, or install in editable/development style. The repository setup metadata installs `toolkit`; `pysot` itself is normally found through the checkout path.
- Config file: an experiment YAML such as `experiments/<experiment>/config.yaml`.
- Dataset paths: every selected `DATASET.<NAME>.ROOT` crop directory and `DATASET.<NAME>.ANNO` JSON file exist.
- Pretrained backbone: most experiment configs set `BACKBONE.PRETRAINED`, commonly under `pretrained_models/`.
- CUDA/distributed availability: `tools/train.py` calls `.cuda()`, initializes NCCL distributed state, and expects launcher environment variables such as `RANK`.
- Output location: `TRAIN.LOG_DIR` and `TRAIN.SNAPSHOT_DIR` are relative to the launch working directory unless made absolute.

Run the safe preflight first:

```bash
python scripts/validate_training_config.py \
  --repo-root <pysot-checkout> \
  --config <experiment-config.yaml> \
  --check-files
```

## Config merge and execution assumptions

`tools/train.py` parses:

```text
--cfg <config.yaml>      default: config.yaml
--seed <int>            default: 123456
--local_rank <int>      supplied by the legacy PyTorch distributed launcher
```

The script then:

1. initializes distributed training through NCCL;
2. merges `--cfg` into the global YACS `cfg`;
3. creates `ModelBuilder().cuda().train()`;
4. loads `BACKBONE.PRETRAINED` relative to the checkout root when set;
5. creates `SummaryWriter(TRAIN.LOG_DIR)` on rank 0;
6. builds `TrkDataset` and a PyTorch `DataLoader`;
7. creates an SGD optimizer and scheduler;
8. resumes from `TRAIN.RESUME`, otherwise loads `TRAIN.PRETRAINED` if set;
9. saves `checkpoint_e<epoch>.pth` files under `TRAIN.SNAPSHOT_DIR` on rank 0.

## Recommended launch patterns

### Run from an experiment directory

This matches the repository's intended output behavior: default `./logs` and `./snapshot` stay under the experiment directory.

```bash
cd <pysot-checkout>/experiments/siamrpn_r50_l234_dwxcorr_8gpu
export PYTHONPATH=../..:${PYTHONPATH}
CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 \
python -m torch.distributed.launch \
  --nproc_per_node=8 \
  --master_port=2333 \
  ../../tools/train.py --cfg config.yaml
```

### Run from the checkout root

Use this form when automation wants all paths relative to the checkout root. Set `TRAIN.LOG_DIR` and `TRAIN.SNAPSHOT_DIR` in the config if you do not want outputs in root-level `logs/` and `snapshot/`.

```bash
cd <pysot-checkout>
export PYTHONPATH=$PWD:${PYTHONPATH}
CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 \
python -m torch.distributed.launch \
  --nproc_per_node=8 \
  --master_port=2333 \
  tools/train.py --cfg experiments/siamrpn_r50_l234_dwxcorr_8gpu/config.yaml
```

### Multi-node template

Run one command on each node. Keep `--master_addr`, `--master_port`, `--nnodes`, and `--nproc_per_node` identical; vary only `--node_rank`.

Node 0:

```bash
cd <pysot-checkout>/experiments/<experiment>
export PYTHONPATH=../..:${PYTHONPATH}
CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 \
python -m torch.distributed.launch \
  --nnodes=2 \
  --node_rank=0 \
  --nproc_per_node=8 \
  --master_addr=<node0-ip> \
  --master_port=2333 \
  ../../tools/train.py --cfg config.yaml
```

Node 1:

```bash
cd <pysot-checkout>/experiments/<experiment>
export PYTHONPATH=../..:${PYTHONPATH}
CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 \
python -m torch.distributed.launch \
  --nnodes=2 \
  --node_rank=1 \
  --nproc_per_node=8 \
  --master_addr=<node0-ip> \
  --master_port=2333 \
  ../../tools/train.py --cfg config.yaml
```

`torch.distributed.launch` is the safest template for unmodified PySOT because the parser declares `--local_rank` and the distributed helper expects legacy launcher environment variables. If using newer `torchrun`, first verify or patch local-rank handling and NCCL initialization.

## Important training keys

| Key | Effect |
| --- | --- |
| `TRAIN.EXEMPLAR_SIZE`, `TRAIN.SEARCH_SIZE`, `TRAIN.BASE_SIZE`, `TRAIN.OUTPUT_SIZE` | Must satisfy `(SEARCH_SIZE - EXEMPLAR_SIZE) / ANCHOR.STRIDE + 1 + BASE_SIZE == OUTPUT_SIZE`; otherwise `TrkDataset` raises `size not match!`. |
| `ANCHOR.RATIOS`, `ANCHOR.SCALES`, `ANCHOR.ANCHOR_NUM` | Anchor count must be `len(RATIOS) * len(SCALES)` and should match `RPN.KWARGS.anchor_num` when configured. |
| `TRAIN.EPOCH`, `TRAIN.START_EPOCH` | Control total training length and resumed epoch indexing. |
| `TRAIN.BATCH_SIZE` | DataLoader batch size per process; global batch is approximately `BATCH_SIZE * world_size`. |
| `TRAIN.NUM_WORKERS` | DataLoader workers per process. Increase only after proving disk/CPU can feed crops. |
| `TRAIN.BASE_LR`, `TRAIN.LR`, `TRAIN.LR_WARMUP` | Scheduler configuration passed to `build_lr_scheduler`. |
| `TRAIN.LOG_DIR` | TensorBoard/log file directory created on rank 0. Relative paths are relative to launch CWD. |
| `TRAIN.SNAPSHOT_DIR` | Checkpoint directory created on rank 0. Relative paths are relative to launch CWD. |
| `TRAIN.RESUME` | Full checkpoint used by `restore_from`; script asserts the file exists before resuming. |
| `TRAIN.PRETRAINED` | Whole-model pretrained weights loaded if `RESUME` is empty. |
| `BACKBONE.PRETRAINED` | Backbone-only weights loaded relative to the checkout root when set. |
| `BACKBONE.TRAIN_EPOCH`, `BACKBONE.TRAIN_LAYERS`, `BACKBONE.LAYERS_LR` | Backbone is frozen initially and selected layers are unfrozen at `TRAIN_EPOCH`. |
| `DATASET.NAMES`, `DATASET.<NAME>.*`, `DATASET.VIDEOS_PER_EPOCH` | Select subdatasets and control sampling length. See [data-formats.md](data-formats.md). |

## Resume and snapshot notes

- On epoch boundaries, rank 0 writes `checkpoint_e<epoch>.pth` under `TRAIN.SNAPSHOT_DIR`.
- `TRAIN.RESUME` should point to one of these checkpoint files and must be readable from every rank.
- If changing GPU count or batch size on resume, verify optimizer state compatibility and learning-rate schedule expectations.
- If only initializing from a trained model, use `TRAIN.PRETRAINED` rather than `TRAIN.RESUME`; if only initializing the backbone, use `BACKBONE.PRETRAINED`.

## What can be verified safely

Verified safe class:

```bash
python tools/train.py --help
python scripts/validate_training_config.py --help
python scripts/validate_training_config.py \
  --repo-root <pysot-checkout> --config <config.yaml>
```

Not a safe default check:

```bash
python tools/train.py --cfg <config.yaml>
```

The direct command usually fails because it lacks distributed `RANK` variables and still reaches CUDA code. Use the distributed launcher only after external prerequisites are confirmed.
