---
name: flower
description: "Route Flower repository tasks for app authoring, strategies and
  mods, local simulation and deployment, Flower Datasets and examples, and
  repository maintenance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Flower

Use this repo skill for the Flower ecosystem: the `flwr` framework, Flower
Datasets, example app patterns, local simulation and deployment workflows, and
repo-maintenance commands for the Flower checkout itself.

## Start here

If you are trying to decide where a task belongs, route by intent:

- **App authoring and customization** → `sub-skills/app-development/`
- **Strategies, aggregation, mods, and checkpoint-aware behavior** →
  `sub-skills/strategies-and-mods/`
- **Local simulation, SuperLink/SuperNode, CLI, and deployment routing** →
  `sub-skills/simulation-and-deployment/`
- **Flower Datasets and example app patterns** →
  `sub-skills/datasets-and-examples/`
- **Contributor commands, public API exposure, protobufs, migrations, and docs** →
  `sub-skills/repository-maintenance/`

## Install and inspect

Work in an isolated Python 3.11 environment and install the Flower packages you
need for the task.

- For ordinary package use and inspection, install `flwr` and `flwr-datasets`.
- For simulation or deployment workflows, add the documented optional runtime
  pieces only when the task actually needs them.
- For maintainer tasks, use the repository's dev commands in the package-owned
  project directory rather than the runtime inspection environment.

A minimal smoke check is:

```bash
python -c "import flwr, flwr_datasets; print(flwr.__version__, flwr_datasets.__version__)"
```

For a more complete read-only smoke, run
[`scripts/check_flower_install.py`](scripts/check_flower_install.py).

## Useful runtime helpers

- [`scripts/check_flower_install.py`](scripts/check_flower_install.py) checks
  package imports, versions, safe CLI help/version output, app-component wiring,
  and tiny Flower Datasets partitioner behavior.
- [`scripts/catalog_examples.py`](scripts/catalog_examples.py) summarizes the
  example app catalog and their dependency surfaces.
- [`scripts/check_public_api.py`](scripts/check_public_api.py) verifies public
  exports for `__all__`-based packages.

## Read next

- [`references/troubleshooting.md`](references/troubleshooting.md) for
  cross-cutting install, import, CLI, optional-dependency, and runtime issues.
- [`references/repo-provenance.md`](references/repo-provenance.md) to decide
  whether this skill matches the current checkout or should be refreshed.
- [`references/repo-routing-metadata.json`](references/repo-routing-metadata.json)
  for router metadata consumed by `repo-skills-router`.

## Package surfaces

The inspected runtime packages expose these public roots:

- `flwr` → `app`, `clientapp`, `serverapp`, `agentapp`
- `flwr_datasets` → `FederatedDataset`, `partitioner`, `preprocessor`,
  `metrics`, `utils`, `visualization`

The sub-skills contain the detailed API notes, workflows, and troubleshooting
for each workflow family.
