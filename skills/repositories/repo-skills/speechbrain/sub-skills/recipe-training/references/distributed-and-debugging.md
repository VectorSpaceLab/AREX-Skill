# Debugging, CPU/GPU, and distributed training

## CPU debug first

Before a full recipe run, prove basic control/data flow:

```bash
python train.py hparams/train.yaml --device cpu --debug --debug_batches 2 --debug_epochs 1
```

If the recipe CSV has tested flags, prefer those exact flags because they match known sample paths and expected outputs.

## GPU single-process run

After CPU debug passes and a CUDA-capable Torch install is verified:

```bash
python train.py hparams/train.yaml --device cuda:0
```

Validate first:

```python
import torch
assert torch.cuda.is_available()
print(torch.cuda.get_device_name(0))
torch.zeros(1, device="cuda")
```

## Single-node DDP

SpeechBrain recommends Distributed Data Parallel for multi-GPU training:

```bash
cd recipes/<dataset>/<task>/<model>
torchrun --standalone --nproc_per_node=4 train.py hparams/train.yaml
```

DDP launches one process per GPU. Batch size is per process/GPU, not automatically divided across all GPUs.

## Multi-node DDP

```bash
torchrun \
  --nproc_per_node=<gpus-per-node> \
  --nnodes=<num-nodes> \
  --node_rank=<rank-of-this-node> \
  --master_addr=<master-host> \
  --master_port=<free-port> \
  train.py hparams/train.yaml
```

Use job-scheduler variables to fill `node_rank`, `master_addr`, and GPU counts. Ensure all nodes see the same dataset paths or use `run_once_per_node`/node-local checkpoint strategies when filesystems differ.

## DDP-safe recipe coding

- Use `speechbrain.utils.distributed.run_on_main` for dataset preparation that should happen once.
- Use `self.device` inside `Brain` methods.
- Avoid hard-coded `cuda:0` in modules or tensors.
- Ensure data preparation writes are visible to other ranks before training begins.
- Use rank-prefixed logging or main-process guards for noisy output.

## Performance and reproducibility notes

- `speechbrain.utils.seed.seed_everything(seed, deterministic=False)` sets Python, NumPy, and Torch seeds, but GPU and distributed runs may still vary.
- Dynamic batching changes memory/time tradeoffs and should be tuned with representative durations.
- Mixed precision (`precision`/`eval_precision`) can accelerate training/inference but may expose numerical or unsupported-op issues.
- `torch.compile` and JIT can fail on some modules; disable them when debugging functional correctness.
