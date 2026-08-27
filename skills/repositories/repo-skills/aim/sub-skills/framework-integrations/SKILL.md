---
name: framework-integrations
description: "Use Aim framework callback integrations, direct tracking
  fallbacks, and TensorBoard conversion while respecting optional dependency
  boundaries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Aim framework integrations

Use this sub-skill when the user needs Aim logging through ML-framework callbacks, loggers, or TensorBoard event conversion/sync. Keep the response focused on integration glue and optional dependency boundaries.

## Route here

- Adding Aim to PyTorch loops, PyTorch Ignite, PyTorch Lightning or Lightning, Hugging Face Trainer, Keras, TensorFlow Keras, XGBoost, CatBoost, LightGBM, Optuna, fastai, Paddle, MXNet, Prophet, stable-baselines3, ACME, or Keras Tuner workflows.
- Diagnosing optional adapter imports or choosing between installing a framework adapter and using direct `Run.track` logging.
- Migrating or syncing TensorBoard event logs into Aim without rerunning training.
- Turning framework-specific metric naming into Aim names, steps, epochs, and contexts.

## Route elsewhere

- Core Aim SDK data model, `Run`, `Repo`, sequence queries, supported Aim object types, and query language: use `tracking-sdk`.
- General CLI, UI/server, remote tracking service, storage/run maintenance, and non-TensorBoard conversion command operation: use `cli-and-services`.
- Frontend implementation, release engineering, Docker builds, or large training-example execution: out of scope for this operating skill.

## Operating rules

1. Treat all framework integrations as optional except direct SDK use. Do not assume that PyTorch, TensorFlow, Lightning, Transformers, gradient boosting libraries, RL libraries, or TensorBoard tooling are installed.
2. Do not run training examples by default. Prefer static callback insertion, parser/help checks, import diagnostics, and direct `Run.track` fallbacks.
3. If an adapter import fails, first identify the missing package, then choose one of two safe paths: install/check the optional dependency only if the user wants that framework callback, or use direct Aim SDK tracking in the training loop.
4. Prefer adapter source signatures over stale example parameter names. Some adapters use `experiment`, while others use `experiment_name`.
5. For TensorBoard migrations, validate the log directory, make the target Aim repository explicit, and use offline conversion unless the user specifically wants live sync.

## What to read

- `references/framework-recipes.md` — callback/logger templates and direct fallback patterns.
- `references/optional-dependencies.md` — optional package probes, adapter import behavior, and installation boundaries.
- `references/tensorboard-and-conversion.md` — TensorBoard conversion and live sync workflows.
- `references/troubleshooting.md` — import failures, parameter mismatches, context issues, TensorBoard cache/dependency failures, and side-effect boundaries.

## Bundled scripts

- `scripts/aim_integration_snippets.py` prints self-contained integration skeletons and can run optional dependency diagnostics without importing heavy frameworks by default.
- `scripts/tensorboard_sync_template.py` validates TensorBoard log directories and prints or explicitly executes a safe `aim convert tensorboard` command; it can also print a live-sync code template.

## Quick response pattern

1. Identify the framework and whether the user wants a native adapter or direct SDK fallback.
2. Check optional dependencies with the bundled snippets script or a minimal import probe.
3. Use the relevant recipe, keeping `repo`, `experiment` or `experiment_name`, `step`, `epoch`, and `context` explicit.
4. If training or service execution is requested, ask for permission and constraints before running it.
