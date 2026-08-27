---
name: nuplan-devkit
description: "Use for Motional nuPlan autonomous-driving planning workflows:
  dataset and map access, scenario filtering, planner implementation, open- or
  closed-loop simulation, metrics, nuBoard, training/preprocessing, nuplan_cli,
  and submission packaging."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# nuPlan devkit

Use this skill for the nuPlan-devkit 1.2.2 Python package and its autonomous
vehicle planning benchmark workflows. It is a router, not a replacement for
the focused sub-skills. Keep the dataset, map version, experiment output, and
backend assumptions explicit before suggesting a command.

## Fast routing

- **Actor states, frames, geometry, trajectories, or tensor transforms:** read
  [`core-geometry`](sub-skills/core-geometry/SKILL.md).
- **Dataset roots, SQLite/ORM queries, sensor blobs, maps, or scenario filters:**
  read [`data-and-maps`](sub-skills/data-and-maps/SKILL.md).
- **Planner code, simulation, metric calculation/aggregation, result files, or
  nuBoard:** read
  [`simulation-and-evaluation`](sub-skills/simulation-and-evaluation/SKILL.md).
- **Feature/target builders, caching, model construction, or training:** read
  [`training-and-preprocessing`](sub-skills/training-and-preprocessing/SKILL.md).
- **`nuplan_cli`, gRPC submission packaging, Docker/EvalAI protocol, or protected
  submission files:** read
  [`submission-and-cli`](sub-skills/submission-and-cli/SKILL.md).

For a task that crosses routes, load the upstream route first: data-and-maps
for a scenario/data question, then simulation-and-evaluation for execution;
training-and-preprocessing shares the scenario/data contract; submission-and-cli
shares the planner trajectory contract.

## Installation and first checks

The package targets Python 3.9+ and exposes the `nuplan_cli` console script.
Use a private environment and install the package with the dependency variant
appropriate to the requested route. The older documented compatibility point
uses NumPy 1.23.4, Hydra 1.1.0rc1, SQLAlchemy 1.4.27, and, for model workflows,
PyTorch 1.9.0 with the repository's matching CUDA wheel on Linux. Do not add
training, CUDA, browser, Docker, or S3 dependencies just to answer a database
or geometry question.

After installation, run the bundled read-only check from this skill directory:

```bash
python scripts/check_environment.py
python scripts/check_environment.py --cuda
nuplan_cli --help
nuplan_cli db --help
```

`--cuda` is optional and only checks a visible CUDA runtime; it does not prove
that a planner or training job fits a particular GPU. The check never downloads
nuPlan data, starts a service, or writes experiment files.

## Required runtime contract

Set these variables before data-backed workflows:

- `NUPLAN_DATA_ROOT`: parent containing `nuplan-v1.1/` DB splits and sensor
  blobs; normally read-only.
- `NUPLAN_MAPS_ROOT`: directory containing map-version metadata and GeoPackages.
- `NUPLAN_EXP_ROOT`: writable experiment/cache/output root.
- `NUPLAN_MAP_VERSION`: usually `nuplan-maps-v1.0` when a map version is needed.

Validate the local layout before invoking a builder, planner, or training job.
Do not let a missing default DB or blob path trigger an implicit download.
Use the data route's validator and stop at a help-only CLI check when data is
not present.

## Verification boundaries

The generated guidance is verified against package source, docs, installed API
signatures, CLI help, static helpers, and selected CPU/mock-native cases. Full
nuPlan dataset downloads, S3 access, Docker Compose, EvalAI uploads, notebook
execution, benchmark-scale training, and portable CUDA performance are
explicitly environment-dependent. Read the relevant troubleshooting reference
before treating a failure as a planner or model defect.

Read [`references/installation-and-environment.md`](references/installation-and-environment.md)
for dependency variants, environment variables, and verification boundaries.
Read [`references/troubleshooting.md`](references/troubleshooting.md) for
cross-cutting import, data, Hydra, backend, and output failures. Read
[`references/repo-provenance.md`](references/repo-provenance.md) before deciding
whether this skill is current for another checkout.

## Handoff discipline

Report the exact package version, dataset split/map version, config overrides,
worker mode, output root, and which backend/data/remote actions were actually
run. Do not claim a full benchmark result from a config parse or a one-batch
smoke test. Keep credentials, private paths, generated reports, and source
checkout assumptions out of reusable instructions.
