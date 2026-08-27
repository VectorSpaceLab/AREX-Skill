---
name: strategies-and-mods
description: "Select, customize, and debug Flower strategies, aggregation
  settings, client mods, and related differential-privacy or secure-aggregation
  behavior."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Flower Strategies and Mods

Use this sub-skill when the task is about choosing a strategy, customizing the
round lifecycle, aggregating metrics, or understanding Flower client mods and
strategy wrappers.

## Read this when

- the task names `FedAvg`, `FedAdam`, `FedAdagrad`, `FedProx`, `FedAvgM`,
  `FedYogi`, `FedMedian`, `FedTrimmedAvg`, `Krum`, `MultiKrum`, `Bulyan`, or
  `QFedAvg`;
- the task says "custom strategy", "override `configure_train`", "change the
  evaluation config", or "use a mod";
- the task mentions differential privacy, secure aggregation, or aggregation
  callbacks.

## Do not route here

- Basic app wiring, `ServerApp`, `ClientApp`, or `tool.flwr.app` config →
  `../app-development/`
- Local simulation, SuperLink/SuperNode, or `flwr run` profile routing →
  `../simulation-and-deployment/`
- Flower Datasets partitioners and example dependency catalogs →
  `../datasets-and-examples/`
- Contributor commands, protobufs, migrations, and repo tests →
  `../repository-maintenance/`

## What to read next

- [references/api-reference.md](references/api-reference.md) for verified strategy
  and mod signatures.
- [references/workflows.md](references/workflows.md) for strategy selection and
  customization patterns.
- [references/troubleshooting.md](references/troubleshooting.md) for skipped
  rounds, aggregation keys, and mod-order issues.
- [`../../scripts/check_flower_install.py`](../../scripts/check_flower_install.py)
  if you also want a safe import/version/CLI smoke from the current environment.

## Core model

A Flower strategy decides which nodes participate in a round, what message
payload to send, how to aggregate replies, and how to interpret the round's
metrics. Built-in strategies give different defaults for sampling, robust
aggregation, optimizer-like behavior, or privacy wrappers.

Client mods are callables that wrap a `ClientApp` before and after a message is
handled. They are the right tool when the behavior change is orthogonal to the
main training or evaluation code.

## When this sub-skill is enough

If the user only needs the strategy or mod logic, stay here. If the request
turns into app structure, runtime routing, or dataset preparation, hand off to
that owner instead of widening this one.
