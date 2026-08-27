---
name: tracking
description: "Routes LabML experiment tracking, logging, configuration,
  monitoring, and AppAPI workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Tracking

Use this subskill for the client-side LabML workflow: recording experiments,
tracking metrics, printing logs, configuring runs, monitoring hardware, and
using the `AppAPI` client.

## Use this when

- The task mentions `experiment`, `tracker`, `logger`, `monit`, `lab`,
  `manage`, `AppAPI`, `.labml.yaml`, `labml monitor`, `labml service`,
  `labml capture`, `labml launch`, or `labml app-server`.
- The user wants to record a run, inspect training progress, publish metrics to
  the monitoring app, or inspect hardware usage.
- The user asks how to integrate LabML into PyTorch, Lightning, Keras, FastAI,
  or similar training code.

## Boundaries

Include:
- Experiment lifecycle helpers and config management.
- Metric tracking, log formatting, and monitored loops.
- Client-side hardware monitoring and service setup.
- App API calls from the client package.
- Framework integration recipes that only need the client runtime.

Exclude or route elsewhere:
- Training-loop abstractions, optimizers, datasets, and helper modules →
  `helpers`.
- SSH, rsync, and remote job orchestration → `remote`.
- FastAPI server internals, MongoDB models, and deployment → `server`.

## Read next

- `references/api-reference.md` for verified signatures, config keys, and CLI
  commands.
- `references/workflows.md` for end-to-end recipes and framework integration
  patterns.
- `references/troubleshooting.md` for missing config files, app publishing,
  monitoring, and service failures.
- `scripts/tracking_smoke.py` for a safe local experiment/checkpoint smoke test.
- `scripts/hardware_probe.py` for a read-only CPU/GPU and monitor capability
  check.

## Typical routes

### Record a run
Choose this route for `experiment.create`, `experiment.record`, `tracker.save`,
`logger.log`, and `monit.loop` requests. It covers both compact scalar logging
and richer tracked outputs.

### Configure a project
Choose this route for `.labml.yaml`, `lab.configure`, dynamic hyperparameters,
run metadata, and git-info questions.

### Monitor hardware
Choose this route for `labml monitor`, `labml service`, `psutil`, and optional
`py3nvml` GPU reporting.

### Use the app client
Choose this route for `AppAPI` requests that read runs, analyses, logs, custom
metrics, or data stores from a monitoring backend.

### Integrate a framework
Choose this route for LabML patterns inside PyTorch, Lightning, Keras, FastAI,
or custom training loops that only need the client package.
