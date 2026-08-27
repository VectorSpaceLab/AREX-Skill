---
name: simulation-and-deployment
description: "Run Flower locally, through the Simulation Runtime, or with
  SuperLink/SuperNode deployment commands and Flower Configuration routing."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Flower Simulation and Deployment

Use this sub-skill for Flower runtime routing: local `flwr run`, the managed
local SuperLink, Simulation Runtime configuration, SuperLink/SuperNode CLI
commands, and deployment-oriented connection/profile setup.

## Read this when

- the task says `flwr run`, `flwr list`, `flwr log`, `flwr stop`, `flwr login`,
  `flwr pull`, `flwr config`, or `flwr federation simulation-config`;
- the task mentions `flower-superlink` or `flower-supernode`;
- the task is about local versus remote profiles, simulation resources, TLS,
  insecure mode, or Flower Configuration.

## Do not route here

- App component wiring or `tool.flwr.app` config → `../app-development/`
- Strategy logic, aggregation, or mods → `../strategies-and-mods/`
- Flower Datasets partitioners and example cataloging → `../datasets-and-examples/`
- Contributor commands, generated-code checks, and repo maintenance →
  `../repository-maintenance/`

## What to read next

- [references/cli-reference.md](references/cli-reference.md) for the command
  families and their meanings.
- [references/workflows.md](references/workflows.md) for local, simulation, and
  deployment flows.
- [references/troubleshooting.md](references/troubleshooting.md) for lock files,
  profile confusion, TLS issues, and Ray/runtime problems.
- [`../../scripts/check_flower_install.py`](../../scripts/check_flower_install.py)
  with `--check-cli` when you want a safe CLI help/version smoke.

## Core model

Flower separates the app entry points from the long-lived runtime processes.
`flwr run` may target the managed local SuperLink, a simulation setup, or a
remote deployment connection depending on the selected profile.

This sub-skill is about choosing the right route and understanding the runtime
lifecycle; it is not where you design the app logic itself.
