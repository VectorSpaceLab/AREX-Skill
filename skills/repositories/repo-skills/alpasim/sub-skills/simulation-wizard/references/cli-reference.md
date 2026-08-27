# Wizard CLI reference

## Entry points

The wizard package exposes:

```bash
uv run alpasim_wizard [group=value ...] [key=value ...]
uv run alpasim_check_config [group=value ...] [key=value ...]
```

Both are Hydra applications. `--help` prints the active config schema and
available groups. `alpasim_check_config` loads catalogs and reports the number
of selected scenes; it does not launch Docker, Slurm, or simulation services.
Use `HYDRA_FULL_ERROR=1` only when a full traceback is needed.

## Required groups and useful groups

A normal managed run needs `deploy`, `topology`, `driver`, and
`wizard.log_dir`. The live public group inventory is:

- `deploy`: `local`, `docker_build_only`, `managed_flashdreams`,
  `external_video_model`
- `topology`: `1gpu`, `2gpu`, `8gpu_12rollouts`, `8gpu_64rollouts`,
  `8gpu_alpamayo1_5_eval`, `8gpu_alpamayo_eval`, `8gpu_no_replicas`, `daemon`
- `driver`: `vavam`, `vavam_video_model`, `alpamayo1`, `alpamayo1_5`,
  `alpamayo1_5_1cam`, `alpamayo1_5_cfg_guidance`, `alpamayo2`, `manual`,
  plus companion config groups
- optional: `driver_source=external_static|external_dynamic`,
  `controller=linear|nonlinear|short_horizon`, `trafficsim=catk|disabled`,
  `physics=disabled|implemented_in_renderer`, camera groups, experiment
  presets, and `chunking=8frame|12frame|16frame`.

Use the exact group spelling shown by the current `--help`; companion `*_configs`
files are implementation defaults and are not usually selected directly.

## Common overrides

```bash
wizard.log_dir=./runs/name
wizard.log_level=DEBUG
wizard.dry_run=true
wizard.run_method=NONE|DOCKER_COMPOSE|SLURM|SLURM_ENROOT
wizard.run_mode=ONESHOT|SERVER
wizard.baseport=6000
wizard.runtime_server_port=6005
wizard.debug_flags.use_localhost=true
wizard.run_sim_services='[driver,renderer,physics,trafficsim,controller,runtime]'
scenes.scene_ids='[clipgt-a,clipgt-b]'
scenes.test_suite_id=public_2601
scenes.limit_to_first_n=1
scenes.local_usdz_dir=/data/usdz
runtime.simulation_config.n_rollouts=2
runtime.simulation_config.control_timestep_us=200000
runtime.simulation_config.assert_zero_decision_delay=true
runtime.endpoints.trafficsim.skip=true
```

`wizard.run_method=NONE` generates artifacts and does not execute a deployment.
`wizard.dry_run=true` causes deployment command dispatchers to log commands
instead of executing them, but context creation can still create directories
and fetch missing scenes. These switches are not equivalent to offline config
composition.

## Debug and daemon modes

For generated-config breakpoint work:

```bash
uv run alpasim_wizard deploy=local topology=1gpu driver=vavam \
  wizard.log_dir=./runs/debug wizard.run_method=NONE \
  wizard.debug_flags.use_localhost=true
```

The generated Compose profile can then be edited/run manually. For a runtime
daemon:

```bash
uv run alpasim_wizard deploy=local topology=1gpu driver=vavam \
  wizard.run_mode=SERVER wizard.log_dir=./runs/server
```

The wizard writes `generated-runtime-server.yaml` with the client-facing host
and port. In server mode, runtime is long-lived; clients should poll the port,
then call the runtime service's info method before submitting work. Runtime RPC
and service semantics belong to `runtime-services`.

## Shell safety

Quote list overrides. Do not put a token in a Hydra override. Quote paths with
spaces, and use a unique `wizard.log_dir` for every trial. Inspect generated
commands before using custom images, external endpoints, `driver_code_hash`,
or mounts. `driver_code_hash` can clone a repository into the run directory and
is not a normal user workflow.
