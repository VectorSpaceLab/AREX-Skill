# Agent API reference

This reference is the implementation contract for NAVSIM agents. Use public
Python imports from the installed package; do not depend on a source checkout
at runtime.

## `AbstractAgent`

`navsim.agents.abstract_agent.AbstractAgent` is a `torch.nn.Module` and an ABC.
Its constructor takes:

```python
AbstractAgent(trajectory_sampling: TrajectorySampling, requires_scene: bool = False)
```

The sampling object is stored as `_trajectory_sampling`, and
`requires_scene` tells evaluation whether the agent needs the privileged
`Scene`. Implement these required methods:

- `name() -> str`: stable human-readable identifier. Evaluation uses it in the
  output CSV filename.
- `initialize() -> None`: per-worker initialization hook. Load checkpoints and
  construct worker-local state here, not in `__init__`.
- `get_sensor_config() -> SensorConfig`: declare exactly which camera/LiDAR
  history is loaded.
- `compute_trajectory(agent_input: AgentInput) -> Trajectory`: required for a
  non-learning agent.

The base `compute_trajectory()` is the learned-agent adapter. It calls every
feature builder, merges their dictionaries, adds a batch dimension to each
feature tensor, calls `forward()` under `torch.no_grad()`, reads
`predictions["trajectory"]`, removes the batch dimension, converts to NumPy,
and constructs `Trajectory(poses, self._trajectory_sampling)`. Override it only
when a non-learning agent computes directly or when a different inference
adapter is intentional.

A learned agent additionally implements:

- `get_feature_builders() -> list[AbstractFeatureBuilder]`;
- `get_target_builders() -> list[AbstractTargetBuilder]`;
- `forward(features: dict[str, Tensor]) -> dict[str, Tensor]`, with a
  `"trajectory"` tensor shaped `[B, T, 3]`;
- `compute_loss(features, targets, predictions) -> Tensor`, returning one
  scalar tensor;
- `get_optimizers()`, returning one optimizer or a dictionary with
  `"optimizer"` and optionally `"lr_scheduler"`;
- optional `get_training_callbacks() -> list[pytorch_lightning.Callback]`.

Do not return a NumPy array or a tensor directly from `compute_trajectory()`.
Do not omit the `"trajectory"` prediction even when adding auxiliary heads.

## Inputs and builders

`AgentInput` contains parallel history lists: `ego_statuses`, `cameras`, and
`lidars`. An `EgoStatus` supplies local ego pose, 2-D velocity, 2-D
acceleration, and a discrete driving command. Sensor objects can be empty when
the selected `SensorConfig` excludes them. Read the latest history item with
`[-1]`; do not assume that a sensor was loaded merely because its dataclass
field exists.

`AbstractFeatureBuilder.compute_features(agent_input)` must use observation
inputs only and return a dictionary of uniquely named tensors. A target builder
uses `compute_targets(scene)` and may read ground truth, maps, annotations, and
future trajectory. Feature and target builder `get_unique_name()` values should
be stable because they identify cached outputs and debugging locations.

A useful custom learned-agent pattern is:

```python
class MyAgent(AbstractAgent):
    def get_feature_builders(self):
        return [MyFeatureBuilder()]

    def get_target_builders(self):
        return [MyTargetBuilder(self._trajectory_sampling)]

    def forward(self, features):
        poses = self.model(features["my_feature"])
        return {"trajectory": poses.reshape(-1, self._trajectory_sampling.num_poses, 3)}
```

The training route supplies target builders with `Scene`; test/submission
inference must remain compatible with the `AgentInput`-only contract.

## Initialization and checkpoints

The built-in learned agents take `checkpoint_path` and load it in
`initialize()`. NAVSIM checkpoints commonly contain a Lightning `state_dict`
whose keys are prefixed with `agent.`. The built-in loading path removes that
prefix before calling the agent's strict `load_state_dict`.

Before a workload:

1. Confirm the checkpoint exists and is a compatible Lightning/PyTorch object
   with a `state_dict` mapping.
2. Confirm the same agent class, architecture configuration, trajectory
   sampling, and latent/non-latent setting were used to produce it.
3. Test CPU loading with `map_location="cpu"` before selecting CUDA.
4. Inspect missing and unexpected keys rather than weakening strict loading;
   a key mismatch usually means the class/config or checkpoint family is
   wrong, not that the error is harmless.
5. Pass a real checkpoint path before `initialize()`; the default `None` is a
   configuration placeholder, not an inference-ready value.

Every distributed worker calls `initialize()`. Keep it idempotent and avoid
writing shared files from that hook.

## Configuration facts

Hydra agent configs instantiate these public classes:

- constant velocity: `ConstantVelocityAgent`;
- privileged human: `HumanAgent`;
- blind learned baseline: `EgoStatusMLPAgent`;
- camera/LiDAR learned baseline: `TransfuserAgent` with `TransfuserConfig`.

The standard agent configuration requests `time_horizon=4` and
`interval_length=0.5`, sets a learning rate for learned agents, and leaves
`checkpoint_path` null until the user supplies one. Preserve the `_convert_:
'all'` behavior when translating the config to another launcher so nested
sampling/config objects arrive as constructor arguments rather than unresolved
configuration nodes.
