---
name: neural-network-components
description: "Routes numpy-ml neural-network component, loss, optimizer,
  scheduler, and toy-model tasks with CPU-only construction guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Neural Network Components

Use this sub-skill for `numpy-ml` tasks that work with NumPy-based neural
network building blocks rather than training a large end-to-end deep-learning
system:

- activations;
- layers and modules;
- losses;
- optimizers and schedulers;
- initializers and wrappers;
- small toy models such as VAE, WGAN-GP, and Word2Vec.

## First Checks

1. Read [`references/api-reference.md`](references/api-reference.md) for the
   constructor signatures and the usual `forward` / `backward` / `update`
   conventions.
2. Run the smoke helper for a tiny CPU-only sanity check:

   ```bash
   python sub-skills/neural-network-components/scripts/neural_component_smoke.py
   ```

3. Read [`references/workflows.md`](references/workflows.md) when you need a
   tiny composition example or a safe pattern for a batch of layers.
4. Read [`references/troubleshooting.md`](references/troubleshooting.md) for
   shape, cache, optimizer, and compatibility failures.

## Route by Task

| User asks for | Use this route |
| --- | --- |
| activation or loss class names and defaults | `references/api-reference.md` and the smoke helper. |
| dense, convolutional, recurrent, attention, embedding, or wrapper layers | layer/module sections of `api-reference.md`. |
| optimizer or learning-rate scheduler choice | optimizer/scheduler sections. |
| VAE/WGAN-GP/Word2Vec construction | toy-model notes in `workflows.md` and `api-reference.md`. |
| feature prep, tokenization, or tabular arrays | route to `../preprocessing-and-utilities/SKILL.md` first. |

## Operating Notes

- This package is a NumPy implementation library; do not imply autograd,
  PyTorch, TensorFlow, or GPU execution as runtime requirements.
- Most methods mutate layer state in place. Keep the object and inspect its
  parameters/derived variables after the call.
- The repo's comparison tests use external frameworks as baselines, but those
  frameworks are optional diagnostics, not the runtime dependency of this
  sub-skill.
