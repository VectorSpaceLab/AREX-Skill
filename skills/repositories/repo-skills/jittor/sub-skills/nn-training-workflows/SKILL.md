---
name: nn-training-workflows
description: "Author and train Jittor models with layers, losses, optimizers,
  schedulers, and state handling."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# nn-training-workflows

Use this sub-skill for Jittor model authoring, scratch training loops, optimizer and scheduler setup, parameter/state handling, gradient accumulation, and train/eval behavior.

## Start here

- Read [`references/nn-api-reference.md`](references/nn-api-reference.md) for the layer, loss, optimizer, scheduler, and init signatures that matter for training.
- Read [`references/training-recipes.md`](references/training-recipes.md) for the bounded quadratic-regression recipe, PyTorch-to-Jittor porting map, accumulation order, and save/load pattern.
- Read [`references/troubleshooting.md`](references/troubleshooting.md) when training fails, loss shapes mismatch, parameters are missing, or state does not reload.
- Run [`scripts/training_smoke.py`](scripts/training_smoke.py) to verify a tiny CPU training loop; it is CPU-safe and network-free by default. Use `--help` first, then `--steps` and `--assert-loss-drop` for a bounded check.

## Use when

- You need to define a model by subclassing `Module` and implementing `execute`.
- You need `nn.Linear`, `nn.Conv`, `nn.BatchNorm`, `nn.Dropout`, `nn.Sequential`, or recurrent layers for a training graph.
- You need `nn.SGD`, `nn.Adam`, `nn.AdamW`, `nn.RMSprop`, `nn.Adan`, `Optimizer.step`, `backward`, `zero_grad`, gradient clipping, or a learning-rate scheduler.
- You need `state_dict`, `load_state_dict`, `save`, `load`, or checkpoint conversion between Jittor and PyTorch-style state bundles.
- You need a bounded recipe for accumulation, clipping, or mode switching.

## Do not use for

- Raw Var or autograd fundamentals.
- Dataset, dataloader, model-zoo, or checkpoint-download workflows.
- Backend flags, compiler setup, or runtime/performance tuning.

## Operating rules

- Implement `execute`, not `forward`.
- Call `model.train()` before training and `model.eval()` before validation or inference.
- Use `optimizer.step(loss)` for the simple case, or `optimizer.backward(loss)` plus `optimizer.step()` when you need accumulation.
- Keep non-trainable state in buffers, not in hidden Python containers.
- Treat `state_dict` shape and name mismatches as a load-time issue to inspect, not something to ignore silently.

## Fast path

1. Confirm the model exposes parameters.
2. Pick the loss whose shape contract matches the target.
3. Choose an optimizer and, if needed, a scheduler.
4. Verify with `scripts/training_smoke.py`.
5. If the loop is unstable, open the troubleshooting reference before changing the architecture.
