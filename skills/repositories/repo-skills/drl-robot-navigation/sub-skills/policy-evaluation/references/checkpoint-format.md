# TD3 policy checkpoint format

## Naming and ownership

The training saver writes two independent PyTorch files using a base name:

| Role | Expected path for base `TD3_velodyne` | Needed for actor-only evaluation |
|---|---|---|
| Actor | `TD3_velodyne_actor.pth` | **Yes** |
| Critic | `TD3_velodyne_critic.pth` | No, but expected for a complete TD3 pair |

The base name is not a directory and must not contain path separators. Resolve it from
the evaluation request or an explicit run manifest; do not silently choose the newest
file. A model directory containing only a critic is not an evaluable policy.

The repository's training `save` method writes `state_dict()` objects rather than a
whole serialized module. The test actor's `load` method expects the actor state dict at
`<directory>/<base>_actor.pth`. This is the compatibility target, not a guarantee that
all files with a `.pth` suffix are safe or relevant.

## Actor schema

The test actor is deterministic and has no target-network or optimizer state. With
`state_dim=24` and `action_dim=2`, the expected keys and tensor shapes are:

| Key | Shape |
|---|---:|
| `layer_1.weight` | `[800, 24]` |
| `layer_1.bias` | `[800]` |
| `layer_2.weight` | `[600, 800]` |
| `layer_2.bias` | `[600]` |
| `layer_3.weight` | `[2, 600]` |
| `layer_3.bias` | `[2]` |

The forward path is `ReLU(layer_1) -> ReLU(layer_2) -> tanh(layer_3)`. A checkpoint
with a different input width, output width, layer width, missing key, unexpected key,
non-tensor value, or incompatible tensor shape must not be forced into this architecture.
A checkpoint saved from a wrapped/module-prefixed model (for example, keys beginning
with `module.`) requires an explicit conversion step outside this skill; do not strip
prefixes implicitly.

## Critic cross-check

The critic is not used to choose an action, but its presence can identify an incomplete
or mixed checkpoint pair. If it is inspected with the optional safe loader, the expected
training keys and shapes are:

| Key | Shape |
|---|---:|
| `layer_1.weight` | `[800, 24]` |
| `layer_1.bias` | `[800]` |
| `layer_2_s.weight` | `[600, 800]` |
| `layer_2_s.bias` | `[600]` |
| `layer_2_a.weight` | `[600, 2]` |
| `layer_2_a.bias` | `[600]` |
| `layer_3.weight` | `[1, 600]` |
| `layer_3.bias` | `[1]` |
| `layer_4.weight` | `[800, 24]` |
| `layer_4.bias` | `[800]` |
| `layer_5_s.weight` | `[600, 800]` |
| `layer_5_s.bias` | `[600]` |
| `layer_5_a.weight` | `[600, 2]` |
| `layer_5_a.bias` | `[600]` |
| `layer_6.weight` | `[1, 600]` |
| `layer_6.bias` | `[1]` |

This is a compatibility cross-check only. It is not a reason to load a critic for an
actor-only run, and it does not validate the quality of the learned policy.

## Safe validation policy

`scripts/check_policy_artifacts.py` performs a non-deserializing inventory by default.
It checks the model directory, basename, regular-file status, and file sizes, then
reports actor and critic readiness. `--load-state-dict` is an explicit opt-in for a
bounded compatibility check. That mode maps to CPU, requires a `weights_only=True`
loader, rejects loaders that cannot provide that argument, applies the configured byte
limit before reading, and checks exact keys/shapes. It never falls back to unrestricted
pickle/module loading.

A presence-only pass is not a load pass. A load pass is not a ROS pass. A ROS pass is
not a policy-quality claim. Record each gate independently.
