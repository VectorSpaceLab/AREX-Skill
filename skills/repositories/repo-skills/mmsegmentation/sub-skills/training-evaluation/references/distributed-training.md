# Distributed and Slurm Training

Use this reference when a user needs multi-GPU, multi-node, Slurm, NPU, or launcher troubleshooting guidance. Runnable examples use bundled skill wrappers; upstream wrapper names are included only to explain the repository behavior they mirror.

## Local Multi-GPU Training

Distributed training launches `torch.distributed` with MMSegmentation's PyTorch launcher mode. The bundled safe equivalent is:

```bash
python skills/mmsegmentation/sub-skills/training-evaluation/scripts/mmseg_train_wrapper.py CONFIG --distributed --gpus GPU_NUM [TRAIN_ARGS...]
```

The launch variables mirrored from upstream are:

```text
NNODES=${NNODES:-1}
NODE_RANK=${NODE_RANK:-0}
PORT=${PORT:-29500}
MASTER_ADDR=${MASTER_ADDR:-127.0.0.1}
```

The resulting launcher command uses:

```bash
python -m torch.distributed.launch \
  --nnodes=$NNODES \
  --node_rank=$NODE_RANK \
  --master_addr=$MASTER_ADDR \
  --nproc_per_node=$GPU_NUM \
  --master_port=$PORT \
  ... --launcher pytorch
```

Examples:

```bash
python skills/mmsegmentation/sub-skills/training-evaluation/scripts/mmseg_train_wrapper.py CONFIG --distributed --gpus 8 --work-dir work_dirs/pspnet
CUDA_VISIBLE_DEVICES=0,1,2,3 python skills/mmsegmentation/sub-skills/training-evaluation/scripts/mmseg_train_wrapper.py CONFIG --distributed --gpus 4 --port 29500
CUDA_VISIBLE_DEVICES=4,5,6,7 python skills/mmsegmentation/sub-skills/training-evaluation/scripts/mmseg_train_wrapper.py CONFIG --distributed --gpus 4 --port 29501
```

Use a different port for concurrent jobs on the same host to avoid `RuntimeError: Address already in use`. Add `--execute` only after the user approves a real distributed job.

## Local Multi-GPU Testing

Distributed testing launches `torch.distributed` with MMSegmentation's PyTorch launcher mode. The bundled safe equivalent is:

```bash
python skills/mmsegmentation/sub-skills/training-evaluation/scripts/mmseg_test_wrapper.py CONFIG CHECKPOINT --distributed --gpus GPU_NUM [TEST_ARGS...]
```

Examples:

```bash
python skills/mmsegmentation/sub-skills/training-evaluation/scripts/mmseg_test_wrapper.py CONFIG CHECKPOINT --distributed --gpus 4
python skills/mmsegmentation/sub-skills/training-evaluation/scripts/mmseg_test_wrapper.py CONFIG CHECKPOINT --distributed --gpus 4 --port 29501 --out work_dirs/format_results
```

## Multi-Node PyTorch Launch

For two nodes with shared networking, run the same wrapper shape on each node with consistent `MASTER_ADDR`, `PORT`, `NNODES`, and per-node GPU count, but different `NODE_RANK`:

```bash
python skills/mmsegmentation/sub-skills/training-evaluation/scripts/mmseg_train_wrapper.py CONFIG --distributed --gpus GPUS_PER_NODE --nnodes 2 --node-rank 0 --master-addr MASTER_HOST --port 29500
python skills/mmsegmentation/sub-skills/training-evaluation/scripts/mmseg_train_wrapper.py CONFIG --distributed --gpus GPUS_PER_NODE --nnodes 2 --node-rank 1 --master-addr MASTER_HOST --port 29500
```

Check these before blaming MMSegmentation:

- `MASTER_ADDR` resolves from every node.
- The selected port is open and not occupied on the master node.
- `NNODES * GPUS_PER_NODE` matches the expected global process count.
- All nodes see the same config, data, checkpoint, and output filesystem or have equivalent paths.
- NCCL or backend-specific environment variables match the cluster's network hardware.

## Slurm Training

Slurm training runs `srun` with MMSegmentation's Slurm launcher mode. The bundled safe equivalent is:

```bash
python skills/mmsegmentation/sub-skills/training-evaluation/scripts/mmseg_train_wrapper.py CONFIG --slurm --partition PARTITION --job-name JOB_NAME [--gpus 4] [--gpus-per-node 4] [--cpus-per-task 5] [--srun-args "..."]
```

The Slurm launch mirrors these resource settings:

```text
--gres=gpu:${GPUS_PER_NODE}
--ntasks=${GPUS}
--ntasks-per-node=${GPUS_PER_NODE}
--cpus-per-task=${CPUS_PER_TASK}
--kill-on-bad-exit=1
```

Example:

```bash
python skills/mmsegmentation/sub-skills/training-evaluation/scripts/mmseg_train_wrapper.py CONFIG --slurm --partition dev --job-name pspnet --gpus 4 --gpus-per-node 4 --work-dir work_dirs/pspnet
```

Port selection for Slurm can be controlled through config overrides or environment variables. Prefer config overrides when possible:

```bash
python skills/mmsegmentation/sub-skills/training-evaluation/scripts/mmseg_train_wrapper.py CONFIG --slurm --partition PARTITION --job-name JOB --gpus 4 --gpus-per-node 4 --cfg-options env_cfg.dist_cfg.port=29500
MASTER_PORT=29501 python skills/mmsegmentation/sub-skills/training-evaluation/scripts/mmseg_train_wrapper.py CONFIG --slurm --partition PARTITION --job-name JOB --gpus 4
```

## Slurm Testing

Slurm testing runs `srun` with MMSegmentation's Slurm launcher mode. The bundled safe equivalent is:

```bash
python skills/mmsegmentation/sub-skills/training-evaluation/scripts/mmseg_test_wrapper.py CONFIG CHECKPOINT --slurm --partition PARTITION --job-name JOB_NAME [--gpus 4] [--gpus-per-node 4] [--cpus-per-task 5] [--srun-args "..."]
```

Example:

```bash
python skills/mmsegmentation/sub-skills/training-evaluation/scripts/mmseg_test_wrapper.py CONFIG CHECKPOINT --slurm --partition dev --job-name pspnet_eval --gpus 4 --gpus-per-node 4 --out work_dirs/format_results
```

## Launcher and Rank Notes

The training and testing workflows accept:

```text
--launcher none|pytorch|slurm|mpi
--local_rank / --local-rank
```

If `LOCAL_RANK` is not already present, the workflow sets it from the local-rank argument. In most ordinary use, do not pass `--local-rank` manually; launchers inject it.

Use `--launcher none` for single-process runs. Use `--launcher pytorch` only under the distributed wrapper or equivalent `torch.distributed` command. Use `--launcher slurm` only under Slurm allocation/wrapper.

## NPU Launch Shape

After installing an NPU-compatible MMCV/backend stack, NPU commands follow the same high-level bundled wrapper shapes:

```bash
python skills/mmsegmentation/sub-skills/training-evaluation/scripts/mmseg_train_wrapper.py CONFIG
python skills/mmsegmentation/sub-skills/training-evaluation/scripts/mmseg_train_wrapper.py CONFIG --distributed --gpus 4
```

Do not assume GPU-specific CUDA diagnostics apply to NPU failures. Check backend installation, device visibility, and the vendor-provided MMCV build first.

## Common Distributed Failure Checks

- Address already in use: change the wrapper `--port`, `PORT`, `MASTER_PORT`, or `env_cfg.dist_cfg.port` so concurrent jobs do not share the same port.
- Hang before first iteration: verify all ranks launched, data paths are visible on every node, and `MASTER_ADDR` is reachable.
- NCCL/backend error: check GPU/NPU driver, backend build, network interface, and CPU-only environment mismatch.
- Wrong number of processes: confirm `--gpus`, `--gpus-per-node`, `--nnodes`, and `--node-rank` values.
- Output collision: give concurrent jobs distinct `work_dir` values or serialize access.
- Slurm job killed: inspect scheduler resource limits, partition constraints, `--srun-args`, `--cpus-per-task`, and wall time before changing MMSegmentation code.
