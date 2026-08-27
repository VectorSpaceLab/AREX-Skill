# Troubleshooting

## Missing or unknown scenario/config

**Symptoms:** the runner cannot find a scenario YAML/module, or an unknown name
is selected.

**Diagnosis:** run the static checker with the intended `--repo-root` and
`--scenario`. It compares module/config stems without importing or running
anything. The runner's source currently imports the scenario module before its
file-existence check and has a typo in the failure message variable, so do not
use the runner as the validator.

**Recovery:** use an exact paired stem from `scenario-catalog.md`; add both the
module with `run_scenario(opt, scenario_params)` and the matching YAML when
developing a new scenario; rerun the checker. Do not accept a filename-only
match if the module lacks `run_scenario`.

## CARLA API or server failure

**Symptoms:** `import carla` fails; connection timeout/refused; blueprint or
map errors; `World loading failed`; a requested town is absent.

**Diagnosis and recovery:**

1. Verify the Python API package and server use the same 0.9.11 or 0.9.12
   release. Run `python -c "import carla; print(carla.__file__)"` in the
   environment used for the CLI.
2. Check `CARLA_HOME`, `CARLA_VERSION`, Python ABI, and the egg path expected
   by `setup.sh`. Reinstall the matching client API rather than mixing release
   files.
3. Start the CARLA server separately and verify the configured port (default
   2000). A client import never proves that a server is reachable.
4. Install the required Town06/Town05 or customized map assets. The guide
   calls out `AdditionalMaps_0.9.1x.tar.gz` for Town06 and a source build for
   customized highway assets.
5. Keep `world.sync_mode: true` and make
   `carla_traffic_manager.sync_mode` match. This source rejects async mode.
6. If the server is running but rendering fails, diagnose GPU/display/Vulkan
   or use an explicitly supported headless setup; do not change the scenario
   configuration to hide a driver failure.

## Optional ML unavailable

**Symptoms:** `--apply_ml` raises an import/model/weights/CUDA error, or a
perception manager cannot initialize.

**Recovery:** first remove `--apply_ml` and set the effective
`vehicle_base.sensing.perception.activate: false` for a baseline if the
scenario supports server-side object information. Do not claim the ML result
was reproduced. For ML mode, install a PyTorch version compatible with the
host's CUDA/CPU and the YOLOv5 integration used by the scenario, then verify
imports and model assets in the same environment. The inspected production
runtime did not verify torch or YOLOv5.

A no-ML run may still require CARLA: the fallback object positions are obtained
from the simulation server, not synthesized locally. Some scenario modules may
also opt into ML-specific behavior independently; inspect the selected module.

## Malformed YAML or bad merge

**Symptoms:** OmegaConf parse error, missing key, interpolation failure, wrong
list length, or a scenario behaves as if defaults disappeared.

**Recovery:**

- Check indentation, colons, quoting, list brackets, and duplicate keys.
- Load the default and scenario files with OmegaConf in a command that does
  not import a scenario module; this catches YAML/interpolation errors without
  starting CARLA.
- Remember that `OmegaConf.merge(default, override)` recursively merges maps,
  replaces scalar values, and replaces lists. It does not concatenate a
  partial list. Use complete `camera.positions`, `vehicle_list`, members, or
  CAV lists when overriding them.
- Preserve `${world.fixed_delta_seconds}` interpolation if a nested controller
  or localization `dt` should follow the world timestep.
- Keep required groups such as `world`, `vehicle_base`, and `scenario`. An
  ML-disabled override changes activation flags; it does not justify deleting
  the sensor/config tree.
- Check that every `spawn_position` has the expected six values, every
  destination has three values, and camera position count agrees with
  `camera.num` before a server run.

## SUMO/co-simulation failure

**Symptoms:** missing `traci`, `SUMO_HOME`, `.sumocfg`/network/route files, or
co-simulation connection failures.

**Recovery:** use only a `*_cosim` scenario with its matching SUMO files;
install SUMO and `traci`, configure the host/port and matching step length, and
verify CARLA and SUMO are both reachable. A CARLA-only scenario does not
become a co-simulation by adding a `sumo` YAML section. SUMO was not verified
in the inspected environment.

## Docker/display failure

**Symptoms:** image build fails downloading CARLA/dependencies, no GPU/Vulkan,
black rendering, X11 permission errors, or OpenSCENARIO is unavailable.

**Recovery:** validate Docker/network/release URLs and build arguments; use a
host-compatible NVIDIA container toolkit and Vulkan/driver mounts; check
`nvidia-smi`/`vulkaninfo --summary`; review X11 authorization before granting
access. The supplied Docker notes explicitly do not support OpenSCENARIO in
this image. Container build success is not a simulation or map-availability
check.
