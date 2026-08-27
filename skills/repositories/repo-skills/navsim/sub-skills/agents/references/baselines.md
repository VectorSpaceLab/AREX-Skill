# Baselines and extension patterns

## Rule-based and privileged agents

### Constant velocity

`ConstantVelocityAgent` is the smallest interface smoke test. It requests no
sensors, reads the latest 2-D ego velocity, computes speed as the Euclidean
norm, and emits a straight local trajectory with constant heading. Each pose is
at `(i + 1) * interval_length * speed` along local x, with y and heading zero.
Use it to validate Hydra instantiation, sensor loading, trajectory row counts,
and output serialization before debugging a learned model.

### Human / privileged

`HumanAgent` is an analysis baseline. It sets `requires_scene=True`, requests no
sensors, and returns `scene.get_future_trajectory(...)`, which uses ground-truth
future ego poses. It is not a deployable or submission agent: submission
creation explicitly rejects any agent with `requires_scene=True`. If a custom
agent needs a scene only for training targets, keep the target builder scene
aware while keeping inference `compute_trajectory(agent_input)` scene-free.

## Ego-status MLP

`EgoStatusMLPAgent` is a blind learned baseline. Its feature builder concatenates
current velocity, acceleration, and the driving command into an `ego_status`
tensor (the standard command representation makes eight input values). It
returns no sensors, builds future trajectory targets from the scene, predicts
`[B, T, 3]`, uses an L1 trajectory loss, and supplies an Adam optimizer.

When extending it:

- keep the feature key and feature dimensionality synchronized with the first
  linear layer;
- use the same `TrajectorySampling` for the final layer size, target builder,
  reshape, and returned `Trajectory`;
- load a checkpoint in `initialize()` and preserve the expected Lightning key
  namespace; and
- treat this as a kinematic/route-intent baseline, not evidence that an agent
  can reason about obstacles without sensors.

## TransFuser

`TransfuserAgent` combines a `TransfuserFeatureBuilder`,
`TransfuserTargetBuilder`, `TransfuserModel`, `transfuser_loss`, Adam, and an
optional visualization callback. The feature dictionary normally contains:

- `camera_feature`: a stitched front-view tensor;
- `lidar_feature`: a BEV histogram tensor; and
- `status_feature`: driving command, velocity, and acceleration.

The target dictionary contains trajectory, fixed-size agent states/labels, and
BEV semantic map. The model returns trajectory plus agent and semantic-map
predictions. Auxiliary predictions are part of the training loss, so a change
to configuration such as detection count, BEV dimensions, or enabled heads must
be reflected in both builders and model/loss expectations.

The standard configuration uses a ResNet image and LiDAR architecture,
256x256-style BEV settings, and the repository's configured detection and
semantic heads. Check the effective configuration rather than assuming those
values when loading a third-party checkpoint.

## Latent TransFuser / LTF

Latent TransFuser is the same public agent with `TransfuserConfig.latent=True`.
The backbone creates a learned positional/latent LiDAR replacement, the
feature builder does not emit a LiDAR feature, and the sensor config requests
only the three current front cameras. The loss also restricts detection targets
to its configured forward angular region. This is an image-only inference mode;
its checkpoint must have been trained with the same latent architecture and
configuration.

A common invalid patch is to set `latent=True` only in the Hydra override while
leaving a custom feature builder, callback, or checkpoint from the normal
LiDAR mode. Verify all three surfaces together: sensor declaration, feature
keys, and state-dict/model architecture.

## Learned hooks checklist

For any new learned agent, verify this sequence before training:

1. `get_sensor_config()` matches every feature actually read.
2. Feature builders use only `AgentInput`; target builders use `Scene` only for
   labels/ground truth.
3. Every returned feature/target key is unique and consumed by the model/loss.
4. `forward()` returns a dict with `[B, T, 3]` trajectory.
5. `compute_loss()` returns one finite scalar for a tiny synthetic batch.
6. Optimizer parameters include the model that `forward()` uses.
7. `initialize()` can load a compatible checkpoint on CPU and does not depend
   on a dataset.
8. `get_training_callbacks()` is optional and must not be required for
   inference.

Use the training route for cache generation, dataset wiring, Hydra overrides,
and expensive training. Use the evaluation route for PDM sampling, metric
caches, traffic policies, and scoring; this route only defines the agent side
of those contracts.
