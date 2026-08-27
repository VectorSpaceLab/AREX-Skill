---
name: engine
description: "Routes Ignite Engine, supervised helper, deterministic, and resume workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Ignite engine workflows

Use this sub-skill when the user is building or debugging the training loop itself: `Engine`, `Events`, supervised trainer/evaluator helpers, resume logic, custom events, or deterministic runs.

## Include here

- `ignite.engine.Engine`, `Events`, `EventEnum`, `State`, and event-handler registration.
- `create_supervised_trainer`, `create_supervised_evaluator`, and the lower-level supervised step helpers.
- `DeterministicEngine`, reproducible dataflow helpers, and state-dict resume behavior.
- Gradient accumulation, AMP/Apex/TPU/MPS variants, and `prepare_batch` / `model_fn` / `model_transform` / `output_transform` customization.
- Training-loop patterns from the MNIST save/resume example, the super-resolution example, the reinforcement-learning examples, and other loop-centric recipes.

## Exclude or route elsewhere

- Checkpoint storage, early stopping, schedulers, progress bars, and logger integrations belong in `sub-skills/handlers/`.
- Metric attachment, metric arithmetic, and metric-family semantics belong in `sub-skills/metrics/`.
- `Parallel`, `idist`, `auto_*`, and backend selection belong in `sub-skills/distributed/`.
- Deprecated `ignite.contrib` compatibility notes live in `references/legacy-contrib.md`.

## Start here

- Read `references/api-reference.md` when you need exact signatures, default behaviors, or parameter semantics.
- Read `references/workflows.md` when you need an end-to-end trainer/evaluator recipe or a resume pattern.
- Read `references/troubleshooting.md` when the loop fails with resume, shape, epoch-length, AMP, or backend errors.
- Run `scripts/resume_smoke.py` for a tiny synthetic loop that exercises supervised training and state-dict resume.

## Common triggers

- "How do I build an Ignite trainer or evaluator?"
- "How do I resume training from a saved state?"
- "Why does `Engine.run` complain about `max_epochs` or `epoch_length`?"
- "How do I use deterministic dataflow or custom events?"
- "How do I switch between CPU, CUDA AMP, MPS, or TPU helpers?"

## Useful boundary notes

The engine route owns the loop skeleton and output semantics, but it does not own storage, logging, or distributed launch details. When a workflow spans engine plus handlers or distributed helpers, keep the training loop here and link the other concerns out to the owning sub-skill.
