---
name: experiment-core
description: "Build, run, and compose Sacred experiments with Experiment,
  Ingredient, Run, captured functions, commands, resources, artifacts, and
  programmatic execution."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# experiment-core

Use this sub-skill when you need to design or modify the Python core of a Sacred 0.8.7 experiment: `Experiment`, `Ingredient`, `Run`, captured functions, commands, hooks, resources, artifacts, scalar metrics, and programmatic execution.

## Read this first

- Read [references/experiment-workflows.md](references/experiment-workflows.md) when implementing a new experiment module, converting plain Python into Sacred structure, composing reusable ingredients, or choosing between `@ex.main`, `@ex.automain`, `ex.run`, and `ex.run_commandline`.
- Read [references/api-reference.md](references/api-reference.md) when you need constructor or method signatures, return-value expectations, special captured arguments, or lifecycle details for `Run` objects.
- Read [references/troubleshooting.md](references/troubleshooting.md) when a run fails around automain placement, interactive/Jupyter safeguards, missing config values, unexpected config injection, read-only config mutation, file tracking, or the “No observers” warning.
- Run [scripts/sacred_experiment_smoke.py](scripts/sacred_experiment_smoke.py) after changing Sacred-related runtime assumptions or validating an installed environment. It uses only temporary files and an in-process `interactive=True` experiment.

## Route elsewhere

- For detailed command-line update syntax, named-config syntax, and CLI flag catalogs, use the `configuration-and-cli` sub-skill.
- For FileStorageObserver, MongoObserver, storage layout, and observer-specific logging persistence, use the `observers-and-logging` sub-skill.
- For seeding, `_seed`/`_rnd`, capture modes, stdout filtering, and reproducibility policy, use the `reproducibility-and-capture` sub-skill.

## Operating rules

- Treat every `@ex.main`, `@ex.automain`, `@ex.command`, `@ing.command`, `@ex.capture`, and `@ing.capture` function as a captured function whose missing parameters may be filled from configuration by name.
- Prefer `@ex.main` plus explicit `ex.run(...)` for tests, notebooks, libraries, and multi-run orchestration. Use `@ex.automain` only in executable scripts and place the decorated function at the end of the file.
- Use `Experiment(..., interactive=True)` with an explicit name for notebook/REPL-style code; otherwise Sacred protects reproducibility by rejecting interactive definitions.
- Use ingredients for reusable configurable components. Their config appears under the ingredient path, and ingredient commands are run by dotted command names.
- Access run-time objects through special captured arguments (`_run`, `_config`, `_log`) rather than globals when possible. Do not mutate `_config` or nested config containers.
- Call `open_resource`, `add_resource`, `add_artifact`, and `log_scalar` only during an active run, either from the `Experiment` object or the captured `_run` object.
