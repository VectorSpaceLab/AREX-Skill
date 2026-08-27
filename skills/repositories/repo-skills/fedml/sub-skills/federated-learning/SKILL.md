---
name: federated-learning
description: "Use FedML for federated-learning simulation,
  cross-silo/cross-device/cross-cloud roles, algorithm flows, and
  privacy/security/analytics variants."
disable-model-invocation: true
metadata:
  disco-role: operating
  parent_skill: "fedml"
license: Apache 2.0
---

# FedML Federated Learning

Use this sub-skill for FedML federated-learning workflows: single-process simulation, MPI/NCCL simulation, cross-silo roles, cross-device/cross-cloud roles, algorithm-flow APIs, and advanced privacy/security/federated-analytics examples.

## Do not use this for

- Ordinary centralized or cross-cloud non-FL training: use `../distributed-training/SKILL.md`.
- Package building or launch submission details: combine with `../launch-and-packaging/SKILL.md`.
- Android or IoT clients: those stacks were excluded from verified runtime coverage.

## Mode selection

| User task | Preferred route |
| --- | --- |
| quick local FL example | single-process simulation (`backend='sp'`) |
| multi-process local simulation | MPI only after host MPI and `mpi4py` are verified |
| GPU/multi-process simulation | NCCL only after CUDA/NCCL/process launch are verified |
| cross-silo server/client job | cross-silo role-specific entry points plus launch/package guidance |
| privacy/security/analytics variant | start from the corresponding `python/examples/federate/*` reference and keep compute/data constraints explicit |

## Core API pattern

```python
import fedml

args = fedml.load_arguments(training_type="simulation", comm_backend="sp")
args = fedml.init(args)
device = fedml.device.get_device(args)
dataset, output_dim = fedml.data.load(args)
model = fedml.model.create(args, output_dim)
runner = fedml.FedMLRunner(args, device, dataset, model, client_trainer=..., server_aggregator=...)
runner.run()
```

Use `sp` for a first smoke unless the task explicitly requires MPI or NCCL.

## Algorithm-flow helper

For a local structural check of FedML's algorithm-flow API without datasets or backend services, run from the root skill directory:

```bash
python sub-skills/federated-learning/scripts/local_algorithm_flow_smoke.py
```

This does not prove full training convergence; it proves a local executor/flow pattern and is safe offline.

## Evidence anchors

- `python/examples/federate/quick_start/parrot/` — quick-start SP simulation examples.
- `python/examples/federate/flow/fedavg/` — algorithm-flow pattern.
- `python/examples/federate/quick_start/octopus/` and `beehive/` — cross-silo package examples.
- `python/examples/federate/security/`, `privacy/`, `federated_analytics/` — advanced variants.
- `python/tests/smoke_test/simulation_mpi/` — MPI smoke reference only; MPI was not verified in the prep environment.

## Backend cautions

- MPI is optional/unverified unless the target environment has `mpirun` and `mpi4py`.
- NCCL requires a compatible GPU/CUDA/NCCL and multi-process launch setup.
- Cross-silo/cross-cloud workflows need consistent YAML, server/client roles, backend env, and often API credentials.
- Do not run host-mutating MPI setup scripts automatically.

## Exit criteria

A federated-learning task is complete when the FL mode, backend, role split, data/model assumptions, and launch-vs-local decision are explicit, and any unverified MPI/NCCL/credential requirements are recorded rather than implied.
