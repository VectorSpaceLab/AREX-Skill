---
name: deployment-and-backends
description: "Routes Mars supervisor, worker, Ray, GPU, Kubernetes, and YARN
  backend requests to verified CLI and prerequisite guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Deployment and Backends

Use this sub-skill when the user asks how to start Mars services, inspect CLI
flags, choose a backend, use GPU placement, or deploy on Ray, Kubernetes, or
YARN. The CPU/local package baseline is verified; optional backend execution is
prerequisite-bound and must not be claimed as verified unless a backend smoke
has passed in the user's environment.

## Trigger phrases

- "Start `mars-supervisor` and `mars-worker`."
- "What flags does `mars-worker` accept?"
- "Use Mars on Ray."
- "Run Mars tensor/DataFrame on GPU."
- "Deploy Mars on Kubernetes or YARN."
- "Set CUDA devices, ports, supervisors, or worker resources."

## What belongs here

- `mars-supervisor` and `mars-worker` CLI help.
- Local cluster startup concepts.
- Ray sessions: `new_session(backend='ray')`, `new_ray_session`, and related
  prerequisites.
- GPU/CUDA tensor and DataFrame placement: `gpu=True`, `to_gpu`, `to_cpu`, and
  worker `--cuda-devices`.
- Kubernetes and YARN cluster APIs and service prerequisites.

## What stays elsewhere

- Local tensor/DataFrame operations -> `tensor-dataframe-core`.
- Remote callable DAGs -> `remote-and-scripts`.
- Mars Learn estimator and optional ML integration APIs ->
  `learn-and-integrations`.

## Read these bundled files

- `references/cli-reference.md` for verified `mars-supervisor` and `mars-worker`
  options.
- `references/backends.md` for Ray, GPU, Kubernetes, and YARN prerequisites.
- `references/troubleshooting.md` for port, optional dependency, device, and
  cluster-tooling failures.
- `scripts/check_mars_cli.py` for a safe CLI help smoke.

## Minimal route

1. For parser or entry-point questions, run the bundled CLI helper or use
   `mars-supervisor --help` and `mars-worker --help`.
2. For local service startup, select supervisor and worker endpoints and ports
   before starting long-running processes.
3. For Ray/GPU/Kubernetes/YARN, verify optional packages and host services
   before running a real backend workflow.
4. When the task needs compute semantics after backend startup, route back to
   the owning tensor/DataFrame, remote, or learn sub-skill.

## Common decisions

- `-h` is help; use `-H` / `--host` for service binding.
- `--cuda-devices ""` disables GPU devices for a worker, while `auto` discovers
  visible CUDA devices.
- Real Kubernetes/YARN examples need external cluster credentials and are not
  safe baseline verification cases.
- The repo's Docker image helper is reference-only because it invokes Docker and
  can push images; do not run it as a bundled runtime script.

## Quality bar

A future agent should be able to list the safe CLI help path, choose the right
backend route, explain missing prerequisites, and avoid accidentally starting
or mutating external cluster resources.
