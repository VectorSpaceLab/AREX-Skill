# Scope and limitations

Read this before a large or externally connected workflow. Earth2Studio is a
composable interface around third-party weather/climate models, checkpoints,
data providers, and optional infrastructure; the Python package alone does
not grant access to those assets.

## Included operating coverage

- Public `earth2studio` component protocols and composition: data/forecast and
  observation sources, lexicons, prognostic/diagnostic/assimilation models,
  IO, perturbations, statistics, utilities, workflows, checkpoints, and serving
  client/server APIs.
- Representative model families and route decisions. Consult the selected
  class's live `input_coords()`/`output_coords(...)`, extra, package, and
  provider terms before use.
- CPU-safe local fixtures and bounded contract checks, plus selected CUDA
  verification when the target environment has a compatible GPU/runtime.

## Not included as runtime dependencies

- Model weights, checkpoint caches, remote data, cloud credentials, CDS keys,
  NGC/Hugging Face access, or private datasets.
- Every model-specific extra. The package metadata declares targeted extras and
  dependency conflicts; install the smallest compatible set for the chosen
  component. Compiled packages such as FlashAttention, natten,
  torch-harmonics, PhysicsNeMo, CuPy, ONNX Runtime GPU, and JAX CUDA need their
  own compatibility checks.
- A running Redis/RQ/FastAPI service, object-storage bucket, auth token,
  signed-URL key, or production deployment. The serving route validates config
  and schemas offline; service lifecycle is an explicit operational step.
- Standalone applications under the repository's recipe collection (evaluation,
  HENS, S2S, tropical-cyclone tracking). Treat them as separate projects with
  their own environments, configs, data, and verification plans.
- Release, CI, license, documentation-build, and process-control automation.

## Verification semantics

- **Import check:** public package/module imports resolve; it does not load
  weights or prove a backend.
- **Contract check:** protocols, coordinates, schemas, shapes, and small local
  transforms behave; it does not prove model accuracy or remote data access.
- **CUDA check:** PyTorch can see and allocate on the target GPU; it does not
  prove every model-specific extension or checkpoint.
- **Native example/test:** a selected bounded repo behavior matches its expected
  signal. Network, credentials, unsafe, expensive, and unavailable optional
  candidates remain explicitly skipped.
- **Production readiness:** requires a separate review of asset licenses,
  data freshness, model memory/performance, service security, observability,
  and recovery policy.

When the source checkout changes public APIs, extras, examples, or behavior,
compare its commit/version/evidence paths with
[repo-provenance.md](repo-provenance.md) and refresh the graph rather than
silently relying on stale guidance.
