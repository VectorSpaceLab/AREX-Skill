# Distributed launch and AMP

## Single-process first

Before using multiple GPUs or mixed precision, prove the selected model can
import, construct, load its checkpoint, and run one small forward on one
visible device. A CPU parser/import check is useful but does not prove CUDA,
NCCL, or FP16 readiness. Keep `-amp` off during a graph/export smoke; the
repository's representative config enables AMP only for non-evaluation
training.

The AMP documentation names NVIDIA Ampere, Volta, and Turing as supported FP16
computing families. The source pattern is `paddle.amp.auto_cast(...)` around
forward/loss and `paddle.amp.GradScaler()` for scale/backward/step/update.
AMP is a training optimization, not a promise that every model exports or that
inference must use FP16. Use FP32 for a first parity comparison.

Representative single-GPU shape (expensive; run only with approval):

```bash
CUDA_VISIBLE_DEVICES=0 python main_single_gpu.py \
  -cfg ./configs/<experiment>.yaml -dataset <name> \
  -batch_size <per_gpu_batch> -data_path <data> -amp
```

The command is a template, not a safe smoke: it may read a large dataset and
write checkpoints/logs. Use a new output path and a bounded local fixture for a
real trial.

## Multi-GPU contract

The repository's documented single-node pattern is:

```bash
CUDA_VISIBLE_DEVICES=0,1 python main_multi_gpu.py \
  -cfg ./configs/<experiment>.yaml -dataset <name> \
  -batch_size <per_gpu_batch> -data_path <data> [ -eval ]
```

The exact parser and model directory win over this template. In the
representative ViT implementation, `main()` creates datasets, calls
`paddle.distributed.spawn(main_worker, args=(config, dataset_train,
 dataset_val))`, and each worker calls `init_parallel_env()`, selects its
rank/world size, builds the dataloader, wraps the model with
`paddle.DataParallel`, and runs. A `DistributedBatchSampler` splits data by
rank. The documented `batch_size` is per GPU, not the global batch size.

Operational checks:

1. `CUDA_VISIBLE_DEVICES` is set before Python starts and contains exactly the
   GPUs intended for this job. Do not assume physical ids remain unchanged;
   inside the process, visible ordinals are remapped.
2. The number of workers requested by the launcher matches visible devices and
   the script's `nprocs`/spawn behavior. Do not nest an external launcher and
   `paddle.distributed.spawn` unless that script explicitly supports it.
3. Every worker can import the same model directory and resolve the same YAML,
   checkpoint, and data paths. Prefer absolute paths for shared files.
4. NCCL, driver, CUDA runtime, and Paddle build are mutually compatible. A
   single-process CUDA failure is fixed before debugging rendezvous.
5. Validation reductions are interpreted correctly. Paddle's default
   `all_reduce` is a sum; the source divides by `world_size` for averages.
6. Only rank 0 should write shared checkpoints/log summaries unless the model
   script has a different documented policy. Concurrent writes can corrupt
   artifacts.

`paddle.distributed.spawn` starts multiple subprocesses and is not a harmless
parallel version of a smoke. It may allocate all requested GPUs, create logs,
write checkpoints, and hang on a bad rendezvous. Never launch it as an
unbounded diagnostic. Start with one GPU, use a tiny local dataset, set a new
output directory, and define a timeout/supervision policy outside this skill.

## AMP and distributed interaction

For distributed AMP, establish both capabilities independently, then combine:

- device probe: compiled CUDA, visible device count, tiny CUDA tensor/layer;
- AMP probe: selected Paddle version exposes the APIs and a tiny approved
  training step works;
- distributed probe: exactly two visible devices, a tiny worker procedure,
  successful init/barrier/exit;
- combined trial: only after the first three pass, with a fixed seed and
  explicit per-GPU batch size.

Do not infer AMP support from GPU presence alone. Do not infer distributed
health from `paddle.device.get_device()` alone. If cuDNN/NCCL is missing,
first classify it as an environment/backend failure and defer both AMP and
multi-GPU claims.

## Failure recovery

- **Only one GPU visible:** inspect the value of `CUDA_VISIBLE_DEVICES`, driver
  visibility, and Paddle's device count. Do not rewrite the model's `NGPUS` to
  hide the issue without recording the reduced run.
- **Hang at spawn/init/barrier:** stop the job safely, check worker count,
  visible devices, rank/world-size logs, and stale rendezvous/processes under
  the job supervisor. Do not repeatedly start more workers.
- **NCCL/all-reduce error:** reproduce with one process, then the smallest
  two-GPU case; preserve the original error and compare driver/Paddle/CUDA
  compatibility. Do not claim CPU as a substitute for NCCL validation.
- **AMP NaN/overflow:** rerun one bounded batch in FP32, inspect loss and data,
  then adjust scaler/model-specific settings only with evidence. Do not label a
  failed AMP run as a model failure.
- **OOM:** lower per-GPU batch or use a smaller approved fixture; remember that
  changing batch size changes optimization and metric comparability.

## Evidence boundary

Primary evidence: `docs/paddlevit-amp.md`,
`docs/paddlevit-multi-gpu.md`, and representative
`image_classification/ViT/main_multi_gpu.py` and `config.py`. Exact launch
flags vary across model families and must be read from their own parsers.
