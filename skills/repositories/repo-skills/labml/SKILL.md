---
name: labml
description: "Guides labml experiment tracking, helper training, remote
  execution, and app-server workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# LabML

Use this skill for the LabML repository family: experiment tracking, logging,
configuration, monitoring, helper training loops, remote job orchestration, and
the LabML monitoring app.

## Start here

- Read `references/package-map.md` to choose the right distribution or install
  set.
- Read `references/workflows.md` when you need a quick workflow map across the
  four major subskills.
- Read `references/troubleshooting.md` when imports, configs, remote jobs, GPU
  monitoring, or the app server fail.
- Read `references/repo-provenance.md` when checking whether this skill matches
  the current checkout or before refreshing it.
- Run `scripts/check_labml_stack.py` for a quick read-only package and backend
  health check.

## Install

Choose distributions and focused extras from `references/package-map.md` rather
than installing every package. The common distribution set is:

```bash
pip install labml labml-helpers labml-remote labml-app
```

For the helper remote-dataset surface, install its direct-import extra:

```bash
pip install 'labml-helpers[remote-dataset]'
```

The `remote-dataset` extra covers `matplotlib`, `urllib3`, `fastapi`, and
`uvicorn` imported by `labml_helpers.datasets.remote`; `labml-helpers[plotting]`
covers the direct `matplotlib` plotting import. These are focused direct
dependencies, not a complete transitive closure or a claim that every workflow
is ready. Training and monitoring examples may additionally need `torch`,
`torchvision`, `psutil`, and `py3nvml`.

The app server additionally needs a running MongoDB service, settings, and
packaged static frontend assets. If the app backend imports but the server
entrypoint fails, read the server sub-skill troubleshooting notes.

## Route map

### `tracking` — `sub-skills/tracking/SKILL.md`
Use this route for:
- `experiment`, `tracker`, `logger`, `monit`, `lab`, `manage`, and `AppAPI`.
- `.labml.yaml` configuration files, run metadata, git metadata, and hardware
  monitoring from the client package.
- `labml` CLI commands such as `capture`, `launch`, `monitor`, `service`, and
  the client-side `app-server` launcher.
- Experiment logging recipes, dynamic configs, and framework integration notes
  for PyTorch, Lightning, Keras, FastAI, and analytics examples.

### `helpers` — `sub-skills/helpers/SKILL.md`
Use this route for:
- `labml_helpers` training-loop utilities, metrics, datasets, `DeviceConfigs`,
  `OptimizerConfigs`, `SeedConfigs`, and the `Module` wrapper.
- `MNISTConfigs`, `CIFAR10Configs`, `TrainingLoopConfigs`, `TrainValidConfigs`,
  `SimpleTrainValidConfigs`, and the remote dataset helpers.
- Small supervised-training recipes, metric wiring, device selection, and
  dataset-serving patterns.

### `remote` — `sub-skills/remote/SKILL.md`
Use this route for:
- `labml_remote` project bootstrap, `.remote/configs.yaml`, rsync-based sync,
  job management, and distributed PyTorch launch helpers.
- Remote server setup, package refresh, command execution, and job tailing.
- SSH, key, exclude-list, and remote-environment troubleshooting.

### `server` — `sub-skills/server/SKILL.md`
Use this route for:
- `labml_app` server startup, REST analysis endpoints, metrics views, custom
  metrics, data stores, and route registration.
- MongoDB-backed app runtime, app settings, analysis registries, and the web UI.
- Server-side deployment, reverse proxy, and runtime troubleshooting.

## What not here

- Do not use this root skill for general PyTorch model design or package-wide
  training helpers; route those to `helpers`.
- Do not use it for SSH orchestration or remote job management details; route
  those to `remote`.
- Do not use it for the monitoring app's backend or deployment details; route
  those to `server`.
- Do not depend on the original repository checkout at runtime; all reusable
  guidance is bundled under `references/` or `scripts/`.

## Quick chooser

- If the user says "track an experiment", "log metrics", "use labml config",
  "monitor hardware", or "use AppAPI", start with `tracking`.
- If the user says "train with helpers", "DeviceConfigs", "TrainValidConfigs",
  "optimizer configs", or "remote dataset", start with `helpers`.
- If the user says "set up remote training", "labml_remote", "job-run", or
  "helper-torch-launch", start with `remote`.
- If the user says "start the app server", "labml_app", "analysis endpoint",
  "custom metric", or "MongoDB-backed UI", start with `server`.
