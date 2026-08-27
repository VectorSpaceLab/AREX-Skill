# Agent troubleshooting

Start with the smallest safe check: import the package, instantiate the
constant-velocity class, run `scripts/validate_agent_contract.py`, and only
then inspect data or checkpoints. Do not respond to an agent error by
launching training, scoring, downloads, or submission generation.

## Install and import

**`ModuleNotFoundError` for NAVSIM, nuPlan, Torch, torchvision, timm, OpenCV,
SciPy, or Lightning**

- Confirm the active Python is the one where NAVSIM and its nuPlan devkit were
  installed; check `python -m pip show navsim nuplan-devkit torch`.
- Use the package's supported Python version and install the matching backend
  dependencies before importing TransFuser. The blind and constant-velocity
  paths are useful for isolating a core import from vision dependencies.
- Import `navsim.agents.abstract_agent` and the constant-velocity class first.
  Import TransFuser only after torchvision/timm/OpenCV and the model backend
  are available.
- Do not solve an import failure by adding local checkout paths to the runtime
  skill or by silently falling back to a different model implementation.

**CUDA or Torch mismatch**

Check `torch.__version__`, `torch.cuda.is_available()`, and the selected device.
A CUDA-enabled wheel can still report unavailable CUDA because the driver or
container is incompatible. Use CPU only for API/import/checkpoint smoke tests;
do not claim TransFuser training or evaluation parity from a CPU import.

## Sensor and optional-backend failures

**`AttributeError`/`NoneType` while processing images or LiDAR**

Compare `get_sensor_config()` with the feature builder. `False` fields and
history lists intentionally produce empty `Camera`/`Lidar` objects. For a
normal TransFuser run, current `cam_l0`, `cam_f0`, `cam_r0`, and current
`lidar_pc` must be present. For latent mode, current LiDAR must be absent and
`TransfuserFeatureBuilder` must skip `lidar_feature`; the backbone supplies
`lidar_latent`. Do not request all sensors merely to hide a mismatch: that
increases I/O and memory and can obscure which history index is wrong.

**History index confusion**

The normal four-frame history uses indices 0 through 3, with 3 current. A list
such as `[3]` is not a frame count and `[0]` is not the current frame. Confirm
`len(agent_input.cameras)`, `len(agent_input.lidars)`, and the selected index
before preprocessing. For a custom temporal agent, document whether it uses
oldest-to-newest order and test that the final item is current.

**TransFuser shape/device errors**

Check camera channel/order and resize first, then LiDAR histogram dimensions,
then status feature length. Keep all feature tensors batched by the base
inference adapter and on the model device during `forward()`. A latent model
must not receive a stale `lidar_feature`; a non-latent model must not receive
`None`.

## Data and configuration validation

**Missing logs, sensor blobs, maps, or cache**

This route cannot make an empty dataset valid. Validate the selected split,
log root, sensor root, map root, and metric-cache path using the setup/data and
evaluation routes before debugging model code. A package import and synthetic
validator intentionally do not prove data availability.

**Hydra cannot instantiate the agent**

Check the `_target_` class name, nested `TrajectorySampling`, `_convert_` mode,
required learned-agent fields (`hidden_layer_dim`, `lr`, `config`), and the
checkpoint path. Keep override names exact: `agent=...`,
`agent.checkpoint_path=...`, and for LTF `agent.config.latent=True`. Print the
effective config when possible rather than debugging a guessed default.

**Sampling or proposal mismatch**

The default agent sampling is a 4-second horizon at 0.5-second intervals. The
standard PDM proposal is 40 poses at 0.1 seconds over 4 seconds. A trajectory
must have exactly `sampling.num_poses` rows and 3 columns. Rebuild both the
model output layer and target builder from the same sampling object; never
reshape to a fixed 40 unless the agent was configured for that sampling.

## CLI/API misuse

**Calling a learned agent with the wrong input**

Call `compute_trajectory(agent_input)` after `initialize()`. Do not pass a
feature dictionary to `compute_trajectory()`, and do not call `forward()` with
unbatched features unless your own adapter adds the batch dimension. Forward
must return a mapping containing `"trajectory"`.

**Calling a privileged agent in submission**

Submission creation provides only `AgentInput`. Any `requires_scene=True`
agent, including the human baseline, is rejected. Move scene-dependent logic to
training targets or rewrite inference to use only ego status and declared
sensors.

**Wrong return type or coordinates**

Return `Trajectory`, not a list, tensor, global pose, or current-plus-future
array. Poses are local rear-axle `(x, y, heading)` values. Run the validator's
wrong-rank and sampling-mismatch cases to reproduce the expected rejection.

## Checkpoints and learned hooks

**Missing/unexpected state-dict keys**

Confirm the checkpoint has a `state_dict`. The built-in loaders remove the
Lightning `agent.` prefix before strict loading. Compare keys after that
normalization against the exact class/config, including latent mode, image and
LiDAR architectures, detection count, BEV settings, and trajectory sample
count. Do not broadly strip arbitrary prefixes or use `strict=False` as a first
fix: it can produce a model that runs with uninitialized layers.

**Checkpoint loads on GPU but not CPU**

Use CPU `map_location` for diagnosis, then compare missing keys and tensor
shapes. A checkpoint can be valid but too large for available memory. Ensure
`initialize()` is called once per worker and that no code moves only part of the
model or feature tensors to CUDA.

**Feature/target key or loss errors**

Compare builder dictionaries and model/loss accesses. Feature builders receive
`AgentInput`; target builders receive `Scene`. Ensure trajectory targets use the
same `num_poses` and that TransFuser auxiliary targets match prediction shapes.
For a tiny synthetic batch, check that loss is scalar and finite before using a
real cache.

**Optimizer or callback appears unused**

Verify the optimizer owns the parameters used by `forward()`. Callbacks are
optional; TransFuser's visualization callback expects its auxiliary outputs,
LiDAR feature, a logger, and a sufficiently large validation batch. Disable the
callback for a minimal inference or loss smoke test rather than changing model
outputs to satisfy plotting code.

## Workflow-specific failures

- **Training cache:** feature caches require the same sensor config and agent
  configuration used at inference. A changed latent flag, history list, image
  transform, or trajectory sampling invalidates old cache entries.
- **Training split:** keep challenge/test/private splits out of training. Use
  the training route to validate split and worker configuration before starting
  a long run.
- **PDM evaluation:** ensure the simulator/scorer proposal sampling agrees and
  that a metric cache covers the selected tokens. Agent failures may be logged
  per token and represented by invalid rows; inspect the first agent exception
  rather than treating a partial CSV as a model success.
- **Two-stage evaluation:** the same agent must satisfy the `AgentInput` and
  trajectory contract for both first-stage and reactive second-stage tokens.
  Do not assume second-stage history has the same synthetic sensor availability
  without checking the loader configuration.
- **Submission pickle:** validate metadata and both stage prediction containers
  locally. Keep private credentials and upload mechanics outside this route;
  never bundle a downloader or uploader as a default agent check.

When the safe validator passes but a data-dependent workflow fails, report the
failure as data/config/backend/workflow evidence rather than weakening the
agent contract.
