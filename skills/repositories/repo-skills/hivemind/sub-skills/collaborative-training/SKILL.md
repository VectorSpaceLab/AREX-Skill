---
name: collaborative-training
description: "Routes Hivemind collaborative-training workflows for averaging
  tensors, wrapping PyTorch optimizers, compression choices, and the ALBERT
  example recipe."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Collaborative Training

Use this route when the task is about peer-to-peer averaging, `hivemind.Optimizer`, `DecentralizedAverager`, `TrainingStateAverager`, compression choices, or the ALBERT collaborative-training example.

## Include

- Direct tensor averaging with `DecentralizedAverager`.
- Wrapped training with `Optimizer`, `TrainingAverager`, `GradientAverager`, `PowerSGDGradientAverager`, and `ProgressTracker`.
- `load_state_from_peers`, state sharing, checkpoint transfer, and local update semantics.
- Compression strategy selection: `Float16Compression`, `Uniform8BitQuantization`, `Quantile8BitQuantization`, adaptive compression, and the optional `BlockwiseQuantization` path.
- The ALBERT example in `examples/albert/`, including data preprocessing, monitor, trainer, and dependency setup.

## Exclude

- DHT bootstrap and connectivity debugging; route that to `dht`.
- Hosted expert servers and remote expert clients; route that to `moe`.
- Benchmarks and stress tests that exist only to measure throughput.

## Start here

1. Read [`references/api-reference.md`](references/api-reference.md) for the verified signatures and important flags.
2. Read [`references/workflows.md`](references/workflows.md) for the generic averaging and optimizer recipes.
3. Read [`references/albert-example.md`](references/albert-example.md) for the end-to-end collaborative ALBERT tutorial.
4. Read [`references/troubleshooting.md`](references/troubleshooting.md) when training stalls, peers diverge, state loading fails, or optional extras are missing.
5. Run [`../../scripts/check_install.py`](../../scripts/check_install.py) with `--check-albert` when you want to validate the optional ALBERT dependency stack.

## What to remember

- `Optimizer` is the main collaborative-training wrapper around a normal PyTorch optimizer.
- `target_batch_size` controls the global epoch boundary; `batch_size_per_step` is the local minibatch contribution.
- `use_local_updates=True` changes the training cadence and disables gradient accumulation semantics.
- `reuse_grad_buffers=True` is memory-efficient but changes how `zero_grad` should be handled.
- Compression defaults are intentionally conservative; use `Float16Compression` or the 8-bit strategies only when the task can tolerate it.
- The ALBERT example adds extra dependencies and data preparation steps that are not part of the base package install.

## Good follow-up questions

- "How do I wrap my PyTorch optimizer with Hivemind?"
- "How do I average tensors or model state across peers?"
- "Why does `load_state_from_peers` fail or time out?"
- "Which compression strategy should I use for training?"
- "How do I run the collaborative ALBERT example?"
