---
name: training-loop-integration
description: "Migrate raw PyTorch training and evaluation loops to Hugging Face
  Accelerate using Accelerator, prepare(), backward(), gradient accumulation,
  dataloader behavior, gather/reduce, mixed precision, DDP kwargs, local SGD,
  communication hooks, and basic distributed logging."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Training Loop Integration

Use this sub-skill when adapting an existing PyTorch model, optimizer, dataloader, scheduler, or evaluation loop to Accelerate while keeping the training code mostly framework-neutral.

## Route first

- For `accelerate config`, `accelerate launch`, launch flags, config files, or process-count setup, use `../configuration-and-cli/`.
- For DeepSpeed, FSDP, TPU, Megatron-LM, FP8 backend recipes, or backend-specific plugin tuning, use `../distributed-training-backends/`.
- For `save_state`, `load_state`, model checkpoint saving, trackers, profiler, or experiment dashboards, use `../checkpointing-and-tracking/`.
- For large-model loading, device maps, offload, or inference dispatch, use the root skill routing to the big-model sub-skill.

## Start here

1. Read `references/workflows.md` for migration recipes and loop patterns.
2. Read `references/api-reference.md` for constructor options, wrappers, dataloader semantics, gather/reduce, kwargs handlers, logging, and scheduler behavior.
3. Read `references/troubleshooting.md` when a distributed loop hangs, metrics are wrong, gradients do not sync, or device placement behaves unexpectedly.
4. Run `scripts/accelerator_loop_smoke.py` to verify a minimal CPU training loop in the current environment.

## Core migration checklist

- Create one `Accelerator` early, before distributed-sensitive objects need its state.
- Remove hard-coded `.cuda()` and direct `.to("cuda")`; prefer automatic device placement through `accelerator.prepare()`.
- Pass related PyTorch objects to `accelerator.prepare(...)` and unpack them in the same order.
- Replace `loss.backward()` with `accelerator.backward(loss)`.
- For accumulation, create `Accelerator(gradient_accumulation_steps=N)` or a `GradientAccumulationPlugin`, then wrap each minibatch body in `with accelerator.accumulate(model):`.
- Use `accelerator.gather_for_metrics(...)` for evaluation metrics and `accelerator.pad_across_processes(...)` before gathering variable-size tensors.
- Use `accelerator.print(...)` or `accelerate.logging.get_logger(...)` instead of unsynchronized process-wide `print()` spam.

## Smoke check

```bash
python skills/accelerate/sub-skills/training-loop-integration/scripts/accelerator_loop_smoke.py
python skills/accelerate/sub-skills/training-loop-integration/scripts/accelerator_loop_smoke.py --help
```

The smoke script is intentionally CPU-safe and tiny. It validates importability, `Accelerator.prepare`, `Accelerator.accumulate`, `Accelerator.backward`, scheduler wrapping, and metric gathering without requiring a distributed launcher.
