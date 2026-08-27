# Cross-cutting troubleshooting

Read this reference when a failure crosses setup, scenario, and module
boundaries. Keep the symptom, the selected backend, and the first failing
layer separate.

## Installation and import

- **`ModuleNotFoundError: carla`:** the CARLA Python API is not installed in
the environment, or its release/Python ABI does not match the server. Install
the official client artifact matching the server and check `python -c "import
carla"`; do not infer server availability from that import.
- **Native extension or NumPy/Pillow errors:** this older release pins legacy
scientific wheels. Use a clean supported Python environment and resolve a
compatible set as a group; run `python -m pip check` and import the specific
module again instead of mixing arbitrary latest wheels.
- **`pip` succeeds but `opencda` imports fail:** verify the editable or normal
package install from the package root, inspect the distribution version, and
then import the failing submodule. Optional modules can fail only when their
route is selected.

## CLI and configuration

- **Unknown scenario or missing YAML:** the scenario name must identify both a
scenario module exposing `run_scenario` and a same-stem YAML override. Use the
bundled static scenario checker before starting CARLA.
- **Malformed or unexpectedly replaced settings:** load the default config and
scenario override with OmegaConf and inspect the merged tree. Nested mappings
are merged; lists and scalar values can be replaced by the override. Preserve
required blocks such as `world`, `vehicle_base`, `scenario`, `controller`, and
`safety_manager`.
- **Unexpected async failure:** this source release expects synchronous mode.
Set `world.sync_mode: true`, use a valid `fixed_delta_seconds`, and keep CARLA
Traffic Manager or SUMO step settings aligned.

## CARLA and maps

- **Connection timeout or `World loading failed`:** start the matching CARLA
server, confirm the configured client port (default 2000), and ensure the
requested Town05/Town06 or custom map is installed. Check client/server release
alignment and display/GPU/headless settings.
- **Blueprint or scenario behavior differs between releases:** pass `-v`
matching the server. OpenCDA has separate vehicle blueprint names for 0.9.11
and 0.9.12.
- **Black rendering/window failure:** diagnose Vulkan/X11/GPU permissions and
server flags independently; Docker GPU visibility is not proof of a usable
CARLA display path.

## Optional ML, SUMO, and ScenarioRunner

- **ML import/model errors:** keep `--apply_ml` false for a baseline. If active
perception is required, install a compatible PyTorch/YOLOv5 stack and model
assets, verify `torch` and the model loader independently, and classify missing
weights or GPU as an external block.
- **`please declare environment variable 'SUMO_HOME'`:** set `SUMO_HOME` to a
real SUMO installation and verify `sumo`, `netconvert`, `traci`, and `sumolib`.
Use the cooperative-simulation preflight checker before a co-simulation launch.
- **TraCI or map conversion failure:** confirm `.sumocfg` references existing
network and route XML files, their basenames are consistent, and the SUMO port
is free. Do not rerun conversion blindly over an existing map.
- **ScenarioRunner import failure:** install the external ScenarioRunner and
OpenSCENARIO dependencies that match the selected CARLA release; the package
import and CARLA client alone do not provide them.

## Runtime cleanup

Wrap live runs so keyboard interrupts still destroy sensor/vehicle actors and
restore world settings. Keep simulator logs and generated evaluation output in
a task-owned output directory. Do not use the bundled static or data helpers
as a substitute for live resource cleanup.
