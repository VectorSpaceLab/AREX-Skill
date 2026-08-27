---
name: alpasim
description: "Use AlpaSim repository guidance for autonomous-driving simulation
  setup, Hydra wizard runs, runtime services, ego drivers and plugins, ASL
  evaluation, controller/physics/traffic components, gRPC contracts, and
  operational troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# AlpaSim

AlpaSim is a modular, data-driven autonomous-driving simulator. It orchestrates
renderer, driver, controller, physics, traffic, runtime, and evaluation
services through gRPC. Use this root as a router; read only the focused
sub-skill needed for the task.

## Route by intent

- **Prepare or run a simulation, compose Hydra overrides, select scenes,
  Docker/Slurm deployment, tune GPUs/timing, or inspect telemetry:** read
  [simulation-wizard](sub-skills/simulation-wizard/SKILL.md).
- **Understand the event loop, service lifecycle, addresses, daemon mode,
  replay, timing validation, renderer caches, or video-model chunking:** read
  [runtime-services](sub-skills/runtime-services/SKILL.md).
- **Select or adapt an ego policy, manual/external driver, model input/output,
  camera rectification, or plugin entry points/config discovery:** read
  [drivers-and-plugins](sub-skills/drivers-and-plugins/SKILL.md).
- **Inspect ASL logs, extract frames, evaluate/aggregate/re-evaluate runs,
  interpret metrics/videos, or use trajectory/geometry utilities:** read
  [evaluation-and-logs](sub-skills/evaluation-and-logs/SKILL.md).
- **Choose MPC, inspect vehicle state, run ground physics, understand CATK
  traffic sessions/handover, or classify CUDA/PyG/Warp requirements:** read
  [control-physics-traffic](sub-skills/control-physics-traffic/SKILL.md).
- **Change protobufs, compile generated stubs, use gRPC clients, inspect
  package entry points, or review safe developer/tool workflows:** read
  [grpc-and-developer-tools](sub-skills/grpc-and-developer-tools/SKILL.md).

Cross-cutting details are in [troubleshooting](references/troubleshooting.md),
[package and backend notes](references/package-and-backend-overview.md), and
[coordinate frames](references/coordinate-frames.md). Run the read-only
[environment checker](scripts/check_env.py) before optional backend work; the
structured [routing metadata](references/repo-routing-metadata.json) is consumed
by the specialized repo-skill importer. Check [repository provenance](references/repo-provenance.md) before treating this
graph as current for another checkout.

## Installation orientation

AlpaSim is a `uv` workspace. The root project intentionally has no default
runtime dependencies; install only the workspace extra for the chosen workflow:

```bash
uv sync --extra wizard                 # wizard and its transitive core
uv sync --extra all                    # all core packages, no optional plugin
uv sync --extra all --extra transfuser # core plus the public Transfuser plugin
```

Use Python 3.11 for the core packages. `alpasim_driver` currently requires
Python 3.12, so use a compatible environment for driver/model inspection. A
full simulation additionally requires Docker Compose, NVIDIA Container
Toolkit/CUDA, scene artifacts, and often Hugging Face access; a package import
is not proof that those services or assets work.

After changing `.proto` definitions, compile stubs from the gRPC package with
`uv run compile-protos`; use the developer-tools route for the safe bundled
compiler and clean/build distinctions. Verify a selected environment with:

```bash
python -c "import alpasim_grpc, alpasim_utils, alpasim_runtime, alpasim_wizard"
python -c "from alpasim_grpc.v0 import runtime_pb2, runtime_pb2_grpc"
```

## Operating boundaries

- Keep `HF_TOKEN`, external endpoints, private paths, model weights, scene
  caches, and scheduler credentials out of prompts, generated YAML, logs, and
  skill content. Treat gated scene/model downloads as user-authorized actions.
- Start with config generation and a one-scene/one-rollout plan. Prefer
  `wizard.run_method=NONE` or a read-only checker before containers, network
  services, GPU inference, or scheduler submission.
- Preserve resolved run files and the first causal service error. A rollout is
  successful only when its `_complete` marker and expected evaluation outputs
  exist; an ASL file alone is not completion.
- Do not use CPU imports to claim CUDA renderer, Warp, CATK/PyG, or model
  inference coverage. The optional backend notes preserve those limits.
- Keep coordinate-frame names explicit: `local`, `rig`, `aabb`, `ecef`, and the
  estimated/noised frame are not interchangeable. Read the coordinate reference
  before changing transforms or service messages.

## Verification entry points

The generated graph is intended to support focused, reproducible checks rather
than a default full simulation. Use the verification artifacts outside this
runtime tree when reviewing coverage. Safe native candidates include wizard
config/dispatch, runtime validation/replay, controller, evaluation/ASL,
utilities, plugin registry, and protobuf compilation tests. Full Docker,
NuRec/FlashDreams, gated HF assets, model inference, CATK compiled extensions,
Slurm submission, and large benchmarks remain explicitly conditional.
