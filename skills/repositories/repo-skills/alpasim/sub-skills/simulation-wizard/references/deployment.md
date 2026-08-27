# Deployment modes and safety boundaries

## Local Docker Compose

`deploy=local` sets the filesystem under the checkout's `data/` by default and
uses the NuRec image configured by the release. The wizard allocates ports from
`wizard.baseport` and generates a Compose file, service commands, volume mounts,
network config, and telemetry files. Docker requires a working daemon,
Compose/buildx plugins, NVIDIA Container Toolkit, and a host driver supporting
the NRE image's CUDA (the public onboarding requirement is CUDA 12.8+ and an
NVIDIA driver in the 570.x-or-newer class).

One-shot managed run:

```bash
uv run alpasim_wizard deploy=local topology=1gpu driver=vavam \
  wizard.log_dir=./runs/local
```

Generated manual run:

```bash
uv run alpasim_wizard deploy=local topology=1gpu driver=vavam \
  wizard.run_method=NONE wizard.log_dir=./runs/generated
cd ./runs/generated
docker compose -f docker-compose.yaml up --remove-orphans \
  --exit-code-from runtime-0
```

The exit-code flag matters because runtime exits at completion while backing
services are long-lived. `wizard.debug_flags.use_localhost=true` makes the
Compose network use host networking and is useful only for controlled mixed
host/container debugging; it increases port-collision risk.

`deploy=docker_build_only` is a config-generation/build-oriented path with
`run_method=NONE` and `dry_run=true`. It still needs a scene-resolvable context
unless the selected config supplies no scenes; do not confuse it with a
complete offline install.

## Managed or external video renderer

Before `deploy=managed_flashdreams`, build the two FlashDreams images with the
FlashDreams project's documented Dockerfiles and ensure the active Docker
context sees `flashdreams-alpasim:local`. This mode uses `pull_policy=never`,
passes `HF_TOKEN` when present, and mounts HF/Torch/FlashDreams caches. It needs
about 48 GB VRAM with the light VaVAM preset and about 96 GB with Alpamayo 1.5,
plus gated model/scene access.

```bash
uv run alpasim_wizard deploy=managed_flashdreams topology=1gpu \
  driver=vavam_video_model +chunking=8frame \
  scenes.test_suite_id=public_2601_video_model \
  wizard.log_dir=./runs/managed-video
```

For an external renderer, start the authorized external OmniDreams gRPC server
using its own deployment documentation, then provide its address:

```bash
uv run alpasim_wizard deploy=external_video_model topology=1gpu \
  driver=alpamayo1_5_1cam +chunking=8frame \
  'wizard.external_services.renderer=["renderer-host:50051"]' \
  wizard.log_dir=./runs/external-video
```

This path does not launch a renderer container. Missing HF credentials may be
optional for a fully cached local scene/model, but they are blocking when the
selected scene or model must be fetched. A dry-run can generate/check the
external endpoint only if scene resolution is local/cached; it cannot prove
renderer reachability, authentication, or GPU/model readiness.

## Slurm and Enroot

Use the site's approved wrapper under its scheduler policy; the repository
submission/resume shell scripts are reference-only because they submit jobs,
change scheduler state, create resume scripts, and depend on allocations,
accounts, `scontrol`, `sacct`, site images, and credentials. Never bundle or run
such a script autonomously.

The wizard supports `wizard.run_method=SLURM` and `SLURM_ENROOT`. Slurm uses
`srun` service steps and site `.sqsh` caches. Direct Enroot requires
`wizard.fuse_dir` and a nonzero active `SLURM_JOB_ID`; it stages squashfs images
and writes job-scoped Enroot runtime/config files. Slurm array jobs split the
resolved sorted scene list round-robin into `generated-user-config-<task>.yaml`
using `SLURM_ARRAY_TASK_ID`, `SLURM_ARRAY_TASK_COUNT`, and task bounds.

`wizard.dry_run=true` prints generated `srun`/Enroot commands and avoids dispatch,
but configuration and filesystem preparation can still happen. Check image
cache paths, host mounts, port visibility, GPU binding, and cluster policy
before removing dry-run.

## Server and external services

`wizard.run_mode=SERVER` keeps the runtime daemon alive and writes
`generated-runtime-server.yaml`. The client-facing port is allocated after
backing service ports unless pinned by `wizard.runtime_server_port`. External
service addresses are added to `generated-network-config.yaml` as unmanaged
endpoints; do not also list that service in `wizard.run_sim_services`.

For `driver_source=external_static`, omit the managed driver service and set
`wizard.external_services.driver=[host:port]`. `external_dynamic` allows a
server client to supply driver addresses per request. `driver=manual` has its
own documented local-driver workflow. These paths require reachable, compatible
gRPC services; the wizard does not validate remote behavior.
