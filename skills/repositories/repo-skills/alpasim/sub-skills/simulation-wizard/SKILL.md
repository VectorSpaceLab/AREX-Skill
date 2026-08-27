---
name: simulation-wizard
description: "Install and operate AlpaSim's Hydra simulation wizard: select
  scenes and drivers, validate configs, generate or run Docker/Slurm
  deployments, tune timing/topology, and inspect run telemetry and outputs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Simulation wizard

Use this route when the task is to prepare, configure, launch, or diagnose an
AlpaSim simulation run. It owns workspace extras, public prerequisites, Hydra
composition, scene/cache selection, deployment choice, capacity/timing knobs,
run-directory interpretation, and Prometheus setup. It does **not** own
microservice implementation/event-loop details, model/plugin contracts, ASL
evaluation, controller/physics/traffic internals, or protobuf development.
Route those topics to [runtime-services](../runtime-services/SKILL.md),
[drivers-and-plugins](../drivers-and-plugins/SKILL.md),
[evaluation-and-logs](../evaluation-and-logs/SKILL.md),
[control-physics-traffic](../control-physics-traffic/SKILL.md), or
[grpc-and-developer-tools](../grpc-and-developer-tools/SKILL.md).

## Operating rules

1. Work from an AlpaSim checkout and use its own `uv.lock`; do not assume a
   bare root `uv sync` installs packages.
2. Treat `wizard.dry_run=true` as command/deployment dry-run only: wizard
   context creation still validates catalogs, creates cache metadata, and may
   download missing scenes. Use a local USDZ directory or an already-populated
   cache for a no-network probe.
3. Never paste HF tokens into commands, generated YAML, or logs. A gated scene
   or model requires the user's own access and `HF_TOKEN`/HF_HOME setup.
4. Generate configs before launching unfamiliar or expensive deployments. Use
   `wizard.run_method=NONE` for a manual Compose/debug workflow; use
   `wizard.dry_run=true` to print deployment commands without starting them.
5. Preserve the resolved `wizard.log_dir`. It is the source of generated
   configs, service logs, rollouts, evaluation products, and telemetry.

## Quick paths

- First local run: install the `wizard` extra, verify Docker/NVIDIA/HF/scene
  prerequisites, then run `deploy=local topology=1gpu driver=vavam` with an
  explicit `wizard.log_dir`.
- Config/catalog check: run `alpasim_check_config` with the same deploy,
  topology, driver, and scene overrides. This queries scene metadata but does
  not launch services.
- Compose generation only: add `wizard.run_method=NONE`; afterward run
  `docker compose -f <log_dir>/docker-compose.yaml up --exit-code-from
  runtime-0` from the generated directory.
- Cluster: choose a site-specific `deploy` and an `8gpu_*` topology through the
  site's approved `sbatch` wrapper. Scheduler submission is an external,
  credentialed action; this skill never autonomously submits it.
- Video model: use `deploy=managed_flashdreams` only with a locally built
  `flashdreams-alpasim:local`, or `deploy=external_video_model` with an
  externally reachable renderer address. Pair single-view driver presets with
  `+chunking=8frame`; do not add ad-hoc camera overrides.

## Core workflow

1. **Install and preflight.** Choose `uv sync --extra wizard` for wizard-only
   work or `uv sync --extra all` for a full core checkout. Compile protobufs
   when service imports need them. Check `uv`, Docker Compose, NVIDIA Container
   Toolkit/CUDA host compatibility, `cargo` if building workspace utilities,
   and HF gated-dataset access. Run the bundled read-only
   [prerequisite probe](scripts/check_prerequisites.py) before changing the
   environment; see [troubleshooting](references/troubleshooting.md).
2. **Select exactly one scene source.** Use `scenes.scene_ids=[...]`,
   `scenes.test_suite_id=public_2601` (recommended broad NuRec suite),
   `public_2601_video_model` (single-view video-model subset), `public_2604`,
   or `public_2507` for historical reproduction. For local artifacts use
   `scenes.local_usdz_dir=<dir>`; the wizard scans `*.usdz`, reads each
   `metadata.yaml`, creates an in-memory `local` suite, and uses that directory
   as the mounted cache. Do not set incompatible `scene_ids` and
   `test_suite_id`; cap with `scenes.limit_to_first_n=N`.
3. **Compose Hydra groups.** Supply `deploy`, `topology`, and `driver` when
   launching the managed driver path. Optional groups include `controller`,
   `trafficsim`, `physics`, `cameras`, `chunking`, `driver_source`, and
   experiment presets. Use `+` only for optional keys (for example
   `+chunking=8frame` or `+runtime.renderer.video_model_config.return_hdmap_frames=true`).
   The complete group inventory and field ownership are in
   the [CLI reference](references/cli-reference.md) and
   [configuration](references/configuration.md).
4. **Check before launch.** Run `alpasim_check_config` with the intended
   overrides. Then use `wizard.run_method=NONE` for generated
   `docker-compose.yaml`, resolved YAML, network addresses, and service
   commands. Inspect mounts, image tags, GPU assignment, scene paths, external
   endpoints, and `assert_zero_decision_delay` before a real run.
5. **Choose deployment.** `deploy=local` uses Docker Compose and the default
   NuRec renderer. `managed_flashdreams` manages a local video-model container;
   `external_video_model` omits the renderer and adds
   `wizard.external_services.renderer=[host:port]`. Slurm and direct Enroot
   require a site wrapper, an active allocation (Enroot), image caches, and
   cluster-specific permissions. Details and safe boundaries are in
   [deployment](references/deployment.md).
6. **Tune a bounded run.** Start with one scene, one rollout, and the smallest
   supported topology. Keep service capacities balanced. Use the timing formula
   in [configuration](references/configuration.md), not rounded frequencies,
   before changing camera/control cadence. Video-model chunk timing has its own
   constraints.
7. **Launch and observe.** Use `uv run alpasim_wizard ...` for a managed run.
   For one-shot manual Compose, use `--exit-code-from runtime-0`; the runtime
   exits while backing services remain servers. For `wizard.run_mode=SERVER`,
   wait for `generated-runtime-server.yaml`'s endpoint to accept connections
   before submitting client RPCs. Inspect telemetry and outputs using
   [scenes and results](references/scenes-and-results.md) and
   [telemetry](references/telemetry.md).
8. **Recover deliberately.** Preserve the run directory and first error. For
   an incomplete run, use the site's approved resume/requeue path and enable
   autoresume only after confirming the original resolved config and scene
   split. Do not delete caches or rerun a gated download blindly.

## Canonical command templates

```bash
# wizard-only environment; run at checkout root
uv sync --extra wizard

# metadata/config check; no services launched
uv run alpasim_check_config deploy=local topology=1gpu driver=vavam \
  scenes.scene_ids='[clipgt-<scene-id>]' wizard.log_dir=./runs/check

# generate Compose/configs without executing services
uv run alpasim_wizard deploy=local topology=1gpu driver=vavam \
  scenes.scene_ids='[clipgt-<scene-id>]' wizard.log_dir=./runs/generated \
  wizard.run_method=NONE

# one-shot default NuRec simulation
uv run alpasim_wizard deploy=local topology=1gpu driver=vavam \
  scenes.scene_ids='[clipgt-<scene-id>]' wizard.log_dir=./runs/vavam

# safe command-only deployment probe (still needs local/cache-resolvable scenes)
uv run alpasim_wizard deploy=local topology=1gpu driver=vavam \
  scenes.local_usdz_dir=./local-usdz wizard.log_dir=./runs/dry \
  wizard.dry_run=true
```

For exact options, output trees, deployment variants, timing math, telemetry,
and recovery, follow the bundled references. They are intentionally
checkout-independent and contain no private environment paths.
