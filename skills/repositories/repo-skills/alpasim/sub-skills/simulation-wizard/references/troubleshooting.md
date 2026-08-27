# Wizard troubleshooting

## Install/import

- **`uv` parse error for `exclude-newer = "3 days"`:** upgrade `uv` (the
  workspace requires a recent version); do not remove the supply-chain guard.
- **Missing `alpasim_wizard` or generated protobuf imports:** use the workspace
  environment and install the appropriate extra. Compile protos from the
  checkout's gRPC package when generated stubs are absent. A bare root `uv
  sync` is intentionally empty.
- **`cargo` missing:** core utilities may need Rust to build `utils_rs`; install
  Rust through the user's approved system process, not from this skill.
- **`CUDA_ERROR_UNSUPPORTED_PTX_VERSION`:** the NRE container needs a host
  NVIDIA driver compatible with its CUDA 12.8 requirement. Check `nvidia-smi`;
  do not diagnose this as a Hydra problem.

## Optional dependencies and backends

- **Docker permission/Compose errors:** verify daemon access, Compose/buildx
  plugins, and NVIDIA Container Toolkit. `wizard.dry_run` avoids dispatch but
  does not prove the daemon or images work.
- **Video model fails to start:** managed mode needs the exact local
  `flashdreams-alpasim:local` image, sufficient VRAM, HF/Torch/FlashDreams
  caches, and model access. External mode needs a reachable compatible gRPC
  renderer. These are required only for that selected path.
- **CATK/physics/model imports fail:** route package/backend details to
  `control-physics-traffic` or `drivers-and-plugins`; a CPU config check does
  not prove CUDA, PyG, Warp, USDZ, or model execution.

## Data and config

- **`GatedRepoError`, 401, or 403:** request access to the gated NuRec dataset
  and export a read-capable `HF_TOKEN`; confirm the selected revision and
  `HF_HOME`. Never put the token in a Hydra override or log.
- **Scene not found:** check the exact ID against the selected catalog, or use
  a suite. A scene ID can have multiple artifact UUIDs; suites pin pairs while
  ID selection chooses the newest artifact.
- **Stale/missing scenes:** inspect `scenes.scene_cache`, release revision, and
  UUID-named `all-usdzs` files. Refresh only the configured cache after checking
  other runs. Local USDZ mode requires valid ZIP metadata.
- **Both scene selectors set:** clear the default `scene_ids` when selecting a
  suite; use one selector. If a local directory is set, its suite is `local`.
- **Missing required config:** provide `deploy`, `topology`, `driver` (unless
  the driver is deliberately external/omitted), and `wizard.log_dir`. Run
  `--help` to see options.

## CLI/API misuse

- **`wizard.run_method=SLURM_ENROOT` rejects launch:** it requires an active
  Slurm allocation and `wizard.fuse_dir`; use the site's allocation workflow.
- **External service conflict:** do not both launch a service in
  `wizard.run_sim_services` and provide its `wizard.external_services` address.
  The wizard rejects a managed driver plus external driver addresses.
- **Runtime server cannot be reached:** use the generated endpoint, wait for
  the port to accept connections, and verify host-network/firewall mapping.
  `generated-runtime-server.yaml` is discovery metadata, not proof of readiness.
- **Port collisions:** choose an unused `wizard.baseport`, avoid unrelated
  host services, and use `use_localhost` only when deliberate.
- **Hydra override errors:** quote list values; use `+` for new optional keys;
  use `runtime.simulation_config...` for runtime fields and
  `wizard...` for deployment fields. Inspect resolved YAML rather than guessing
  which group owns a key.

## Workflow failures

- **No `rollouts/` directory or runtime exits:** inspect `txt-logs` and the
  first failing service, then inspect `wizard-config.yaml`, network config,
  mounts, image tags, and scene path. Generated configs alone do not mean the
  run ran.
- **Compose hangs after success:** include `--exit-code-from runtime-0`; other
  services are long-lived.
- **Zero-delay misalignment:** if camera interval `f` does not divide the
  control interval `c` (or vice versa for the intended schedule), the last
  frame may not finish at the decision boundary. Example `f=100000`,
  `c=150000`: first decision at 150000 has no aligned camera completion.
  Choose `c=N*f`, align pose reporting, or adjust driver subsampling. Keep
  `assert_zero_decision_delay=true` while correcting it.
- **External renderer/driver dry-run with missing HF token:** config generation
  can still be blocked by scene acquisition before it ever tests the remote
  endpoint. Use an already cached scene or valid local USDZ to reach generation;
  classify missing HF access as blocking for uncached scene/model acquisition,
  but optional for fully cached inputs. A dry-run never proves remote renderer
  reachability, model loading, or GPU readiness.
- **Video-model drift/misalignment:** retain recorded camera count/calibration;
  use the matching single-view preset and chunking preset. If debug HD map
  frames are enabled, compare them with the recorded seed view.
- **Telemetry absent:** check `wizard.prometheus.start_prometheus`, generated
  target files, allocated ports, and `txt-logs`; an external Prometheus may be
  intended instead. Do not run the SSHFS/Docker dashboard launcher blindly.
- **Slurm/enroot failure:** check allocation, `srun` overlap/CPU binding,
  `.sqsh` cache visibility, FUSE tools, node-local cache, and job-scoped
  Enroot paths. Do not retry scheduler submission repeatedly without preserving
  the job log and reason.
