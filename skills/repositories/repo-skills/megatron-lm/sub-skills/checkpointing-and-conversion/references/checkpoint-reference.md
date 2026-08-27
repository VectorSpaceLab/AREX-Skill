# Checkpoint reference

## Distributed checkpoint formats

Megatron Core uses distributed checkpoints to save/load sharded model and optimizer state across tensor, pipeline, data, expert, and FSDP layouts.

| Format | Use when | Notes |
|---|---|---|
| `torch_dist` | General Megatron distributed checkpointing. | Supports model resharding when sharded state dict metadata is available. |
| `fsdp_dtensor` | Megatron-FSDP / DTensor checkpointing. | Use with `--use-megatron-fsdp` and FSDP sharding. |
| legacy `mp_rank_*` | Older checkpoints. | Not supported by newer GPT-Hybrid converter paths; convert/resave through a supported format when possible. |

## Optimizer state formats

For distributed optimizer state, distinguish:

- `dp_reshardable` (default in newer flows): fast, but not fully reshardable across arbitrary model-parallel changes.
- `fully_reshardable` / model-space optimizer state: slower, but supports changing parallelism on load.

When a user wants to change TP/PP/EP/FSDP and continue optimizer state, include:

```bash
--dist-ckpt-optim-fully-reshardable
```

If the checkpoint was saved in an older or bucket-space format, the model weights may still load while optimizer state cannot. Use `--no-load-optim` for weights-only continuation or resave with a compatible format.

## Safe checkpoint loading

PyTorch 2.6 changed default `torch.load` behavior toward safer `weights_only=True` loading. If loading a checkpoint fails with an unsupported global such as `argparse.Namespace`:

```python
import argparse
import torch

torch.serialization.add_safe_globals([argparse.Namespace])
```

Only allow-list the exact classes required by the trusted checkpoint. Do not globally disable safe loading just to silence the error.

## Async checkpointing

Megatron supports asynchronous checkpoint saves. Newer flows are moving toward NVRx (`nvidia-resiliency-ext`) for async strategy support. If an async strategy is missing:

- Check whether `nvidia-resiliency-ext` is installed for the selected environment.
- Use the documented `--async-strategy` flag when selecting legacy vs NVRx behavior.
- Do not treat async-save failure as a model-shape issue; separate storage/backend dependencies from checkpoint metadata.

## Resume semantics

| Intent | Flags/behavior |
|---|---|
| Full resume | Use `--load` and allow optimizer/RNG/scheduler state to load. |
| Finetune from weights | Use finetune semantics and usually skip optimizer/RNG state. |
| Weights-only recovery from incompatible optimizer | Use `--no-load-optim` and possibly `--no-load-rng`. |
| Save new checkpoint root | Use `--save` and ensure shared writable storage. |
| Change format/layout | Use compatible distributed format and validate optimizer state resharding. |

## Tracker/root layout

Standard training expects a checkpoint root with a tracker file such as `latest_checkpointed_iteration.txt`. Some conversion tools can operate on a direct metadata directory, but a flat output without the tracker may not be consumable by ordinary training entrypoints without additional handling.
