---
name: grpc-and-developer-tools
description: "Maintain AlpaSim protobuf and gRPC contracts, use generated stubs,
  inspect installed packages and entry points, and perform safe
  contributor/tooling checks without starting simulation or external
  infrastructure."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# gRPC and developer tools

Use this sub-skill when the task is about the AlpaSim protobuf contract,
generated Python modules, service-client examples, package metadata, plugin
entry points, contributor checks, map-tool boundaries, telemetry inspection,
or deciding whether a helper is safe to run. This is a developer/API skill,
not a simulation operator.

## Route first

- For installation, Hydra composition, local/Docker/Slurm deployment, scene
  caches, or run telemetry operation, use
  [simulation-wizard](../simulation-wizard/SKILL.md).
- For service lifecycle, runtime orchestration, replay, timing, or service
  implementation, use [runtime-services](../runtime-services/SKILL.md).
- For model/plugin behavior or driver configuration, use
  [drivers-and-plugins](../drivers-and-plugins/SKILL.md).
- For ASL inspection, metrics, map/trajectory analysis, or result evaluation,
  use [evaluation-and-logs](../evaluation-and-logs/SKILL.md).

## Fast workflow

1. Identify the installed `alpasim_grpc` version and the exact `.proto` or
   service involved. Do not infer a message name from a nearby service.
2. For a schema change, preserve package names, field numbers, and import
   paths; regenerate all Python artifacts using the package build/compile
   workflow. Never hand-edit generated `*_pb2.py`, `*_pb2_grpc.py`, or `.pyi`
   files.
3. Inspect the diff, import the generated modules, and run a focused native
   test plus formatting/static checks before proposing a service change.
4. For a plugin or package change, inspect its declared entry-point group,
   import target, dependency direction, and optional backend requirements.
5. Keep scheduler submission, SSHFS mounts, Docker launchers, model downloads,
   and full simulations as explicit user-approved operations. This sub-skill
   only supplies safe inspection and generation guidance.

Detailed API facts and service grouping are in
[references/grpc-api.md](references/grpc-api.md). Read
[tools and safety](references/tools-and-safety.md) before a helper; the
[protobuf compiler](scripts/compile_protos.py) is the bundled non-destructive
path for explicit source/output roots. The contributor sequence and
review checklist are in [references/developer-workflows.md](references/developer-workflows.md).
Use [references/tools-and-safety.md](references/tools-and-safety.md) before
running helper commands and [references/troubleshooting.md](references/troubleshooting.md)
for recovery.

## Generated API use

The public generated package is `alpasim_grpc.v0`. Typical client imports are:

```python
import grpc
from alpasim_grpc.v0 import common_pb2, sensorsim_pb2
from alpasim_grpc.v0.sensorsim_pb2_grpc import SensorsimServiceStub

with grpc.insecure_channel("host:port") as channel:
    stub = SensorsimServiceStub(channel)
    request = sensorsim_pb2.RGBRenderRequest(scene_id="scene_id")
    # response = stub.render_rgb(request, timeout=10)
```

Use the actual generated message and stub names; for example, the render
message is `RGBRenderRequest`, not a generic `RenderRequest`. A channel/client
smoke test proves serialization and stub construction, not that a renderer or
other service is running. Route service implementation and health diagnosis to
`runtime-services`.

## Commands and gates

- In an installed package, use `uv run compile-protos` and
  `uv run clean-protos` only from the gRPC package's own project context. The
  bundled helper at [scripts/compile_protos.py](scripts/compile_protos.py) is
  for explicit source and output paths and is non-destructive by default.
- For a proto edit, compile, inspect generated-file changes, run generated
  imports, then run the narrowest relevant test. A successful compile does not
  establish wire compatibility.
- Run `uv run pytest <focused-test>` for safe unit cases and
  `pre-commit run --all-files` for contributor-facing changes when the
  repository environment is available. Do not substitute a broad simulation
  run for these checks.
- `alpasim-info` reports installed model, MPC, scorer, tool, and config entry
  points. It may enumerate optional model imports; treat a timeout or logged
  load warning as an optional-dependency issue, not proof that the registry is
  empty.

## Boundaries and handoff

This skill documents map visualization and telemetry/scheduler helper safety,
but does not launch them. A map helper may require an artifact and optional
geometry/plotting packages; use a disposable output location and route actual
map interpretation to `evaluation-and-logs`. Prometheus/Grafana and Slurm
helpers can mount, chmod, submit, requeue, or create files outside the project;
read their help and obtain explicit approval first. Never copy credentials,
model weights, scene caches, SSH paths, or scheduler allocations into a skill.

When handing off, report: schema/package touched, generated files checked,
commands and tests run, optional dependencies skipped, and whether the
operation contacted a service, scheduler, network, Docker, or filesystem mount.
