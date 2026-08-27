# Tools and safety boundaries

## Safe by default

| Operation | Safe procedure | What it does not prove |
|---|---|---|
| Package import | Import `alpasim_grpc.v0` generated modules and inspect descriptors | Endpoint health, scene/model availability, or backend support |
| Proto generation | Use the bundled helper with explicit roots; default mode only writes generated outputs | Wire compatibility or caller correctness |
| Plugin listing | Use `importlib.metadata` or `alpasim-info` in an isolated environment | That every optional plugin can load or run inference |
| Serialization | Round-trip a tiny in-memory protobuf fixture | Service semantics or timing |
| Unit tests | Run focused fixture-based pytest targets | A full GPU/container simulation |
| Static checks | Run pre-commit on the intended diff | Runtime integration |

The bundled compiler writes only under the explicit output root. It never
fetches dependencies, contacts a service, starts Docker, submits a job, or
reads credentials. Do not pass a production package directory as output unless
the user explicitly intends to regenerate it; use a disposable copy for a
first run.

## Map utility boundary

The map plotting utility accepts an artifact archive and can render XODR or
clip-style map data, with optional route preview. It relies on plotting,
trajectory/map, artifact, and parquet dependencies and may open a GUI or write
a PNG. Use `--no_block` and a non-GUI backend in headless checks, keep input
artifacts read-only, and direct map interpretation or evaluation to
`evaluation-and-logs`. Do not bundle artifacts or hard-code their paths.

## Telemetry boundary

AlpaSim runs publish Prometheus file-SD targets and write run metrics; a run
can produce `metrics_plot.png`. The optional Prometheus/Grafana helper is not a
read-only inspector: it requires Docker, may create a working directory, and
can use SSHFS for a remote file-SD source. Mounting/unmounting, remote
directory creation, permission changes, and container startup require explicit
approval. Prefer inspecting existing run metadata or metrics through the
simulation/evaluation owners.

## Slurm boundary

The Slurm submit helper validates required Hydra groups and forwards overrides,
but it also creates log/resume/reevaluation files, sanitizes inherited
scheduler environment, starts the wizard, and may requeue a job. The resume
helper reads a prior run's config and submits another job. Both require a
cluster, allocation, scheduler state, and user authorization. Only run the
fixture-based submit unit test in a contributor check; never replace it with
`sbatch` during skill use.

## Other exclusions

Do not copy or invoke model/scene downloads, external renderer launchers,
credentialed Hugging Face operations, SSH commands, Docker image builds, or
large benchmark sweeps as a validation shortcut. Report the missing backend or
permission and keep the capability classified as optional or unverified.
