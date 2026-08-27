# Network And Saver Workflows

Use this reference when adapting Acme TensorFlow/Sonnet networks, losses, save/restore behavior, variable syncing, or Launchpad TF examples. The examples are intentionally self-contained patterns, not instructions to open source examples.

## Core Sonnet Model Contract

Acme TF agents expect Sonnet modules or TensorFlow callables with TensorFlow tensors in and tensors or TensorFlow Probability distributions out.

Typical imports for real execution:

```python
import sonnet as snt
import tensorflow as tf
import tensorflow_probability as tfp

from acme import specs
from acme.tf import networks
```

Useful building blocks from `acme.tf.networks` include:

| Need | Building blocks |
| --- | --- |
| Flatten/concatenate nested observations | `acme.tf.utils.batch_concat`, `networks.CriticMultiplexer` |
| MLP torso for continuous control | `networks.LayerNormMLP`, `networks.NearZeroInitializedLinear`, `networks.LayerNormAndResidualMLP` |
| Stochastic continuous policy | `networks.MultivariateNormalDiagHead`, `networks.StochasticModeHead`, `networks.StochasticSamplingHead`, `networks.ExpQWeightedPolicy` |
| Distributional critic/Q head | `networks.DiscreteValuedHead`, `networks.DiscreteValuedDistribution`, `networks.GaussianMixture`, `networks.MultivariateGaussianMixture` |
| Discrete Q/value networks | `networks.DuellingMLP`, `networks.DiscreteFilteredQNetwork`, `snt.Linear(num_actions)` |
| Atari/vision torsos | `networks.AtariTorso`, `networks.DQNAtariNetwork`, `networks.R2D2AtariNetwork`, `networks.IMPALAAtariNetwork`, `networks.ResNetTorso`, `networks.DrQTorso` |
| Recurrent networks | `networks.DeepRNN`, `networks.LSTM`, `networks.CriticDeepRNN`, `networks.RNNUnpackWrapper`, `networks.RecurrentExpQWeightedPolicy` |
| Legal-action masking | `networks.MaskedSequential`, `networks.EpsilonGreedy`, `networks.NetworkWithMaskedEpsilonGreedy` |
| Action bounds | `networks.TanhToSpec`, `networks.RescaleToSpec`, `networks.ClipToSpec` |
| Utility wrappers | `acme.tf.utils.create_variables`, `acme.tf.utils.to_sonnet_module`, `acme.tf.utils.to_numpy_squeeze`, `acme.tf.utils.zeros_like` |

## Continuous Control Networks

### DDPG/D4PG Style

Use deterministic policy and critic modules. D4PG commonly uses a distributional critic head; DDPG commonly uses a scalar critic head.

```python
policy_network = snt.Sequential([
    networks.LayerNormMLP((256, 256, 256), activate_final=True),
    networks.NearZeroInitializedLinear(action_spec.shape[-1]),
    networks.TanhToSpec(action_spec),
])

critic_network = snt.Sequential([
    networks.CriticMultiplexer(),
    networks.LayerNormMLP((512, 512, 256), activate_final=True),
    networks.DiscreteValuedHead(vmin=-150.0, vmax=150.0, num_atoms=51),
])

observation_network = snt.Sequential([tf.identity])
```

Validation checklist:

- Call `acme.tf.utils.create_variables(policy_network, [environment_spec.observations])` for policy-only modules when practical.
- For critic networks, test a batched `(observation, action)` pair because `CriticMultiplexer` expects both inputs.
- Confirm policy output shape matches `environment_spec.actions.shape` and dtype is compatible with the bounded action spec.
- For D4PG/DMPO distributional critics, confirm the critic returns a `DiscreteValuedDistribution`-like object with values/logits rather than a scalar tensor.

### MPO/DMPO/MO-MPO Style

MPO variants use stochastic policies, critic networks, and optional shared observation networks.

```python
policy_network = snt.Sequential([
    networks.LayerNormMLP((256, 256, 256), activate_final=True),
    networks.MultivariateNormalDiagHead(action_spec.shape[-1]),
])

greedy_policy_for_eval = snt.Sequential([
    policy_network,
    networks.StochasticModeHead(),
])

critic_network = snt.Sequential([
    networks.CriticMultiplexer(),
    networks.LayerNormMLP((512, 512, 256), activate_final=True),
    snt.Linear(1),
])
```

Notes:

- `MPO` and `DistributionalMPO` constructors accept `policy_loss_module`; distributed variants accept `policy_loss_factory`.
- Use `acme.tf.losses.MPO` for standard MPO loss and `acme.tf.losses.MultiObjectiveMPO` for MO-MPO.
- `num_samples` controls sampled actions used by MPO-style policy improvement.
- Shared `observation_network` is useful for pixels; policy and critic then act as heads over embedded observations.

## Discrete And Recurrent Networks

### DQN / DQfD / BCQ

Discrete Q agents usually need a network ending in one Q-value per action.

```python
network = snt.Sequential([
    networks.AtariTorso(),
    snt.Flatten(),
    snt.nets.MLP([512, action_spec.num_values]),
])
```

For small Bsuite-style observations, replace the torso with `snt.Flatten()` and an MLP. For DQfD or BCQ, ensure the dataset fields match the transition structure expected by the learner; route replay and dataset shape details to `replay-and-data`.

### R2D2 / R2D3 / IMPALA

Recurrent agents use `snt.RNNCore`-compatible networks.

- R2D2/R2D3 networks should expose an initial state and produce Q-values while consuming sequences with burn-in and trace lengths.
- IMPALA networks produce policy logits and baseline/value outputs; `networks.PolicyValueHead(num_actions)` is a common head.
- Use `networks.DeepRNN([...])` or a custom `networks.RNNCore` subclass when stacking torsos, LSTMs, and heads.
- Keep `sequence_length`, `sequence_period`, `burn_in_length`, `trace_length`, and replay sequence settings consistent with the replay/data sub-skill.

## OpenSpiel And Legal Actions

OpenSpiel observations carry legal-action information. Use legal-action-aware wrappers so invalid moves cannot be selected.

```python
network = networks.MaskedSequential([
    snt.Flatten(),
    snt.nets.MLP([64, 64, action_spec.num_values]),
    networks.EpsilonGreedy(epsilon=0.1, threshold=-1e8),
])
```

Checklist:

- Make sure the observation object includes the legal-actions mask field expected by the OpenSpiel wrapper.
- The final Q/logit dimension must equal the number of discrete actions.
- `EpsilonGreedy` uses a threshold to identify legal actions; set the threshold below valid action values and above the illegal penalty used by the mask.
- Prefer the OpenSpiel environment loop route in `core-workflows` for loop mechanics; keep TF network masking here.

## Launchpad Distributed Workflow

A distributed TF example should keep these pieces separate:

1. Parse flags and environment identifiers.
2. Define `environment_factory(evaluation: bool = False)`.
3. Define `network_factory(action_spec)` or `network_factory(environment_spec)` that returns fresh Sonnet modules.
4. Construct a distributed agent builder such as `DistributedD4PG`, `DistributedDistributionalMPO`, `DistributedMPO`, `DistributedDQN`, `DistributedR2D2`, or `DistributedIMPALA`.
5. Build the Launchpad program with `program = program_builder.build(name='...')`.
6. Launch locally with a Launchpad launch type such as `local_mt` for debugging or `local_mp` when process isolation matters.

Minimal launcher skeleton:

```python
import launchpad as lp
from acme.agents.tf import dmpo

program_builder = dmpo.DistributedDistributionalMPO(
    environment_factory=environment_factory,
    network_factory=network_factory,
    num_actors=4,
    environment_spec=environment_spec,
)
program = program_builder.build(name='dmpo_control_suite')
lp.launch(program, launch_type='local_mt')
```

Validation checklist:

- `environment_factory` must not capture a mutable environment instance; it should create a new one per actor/evaluator.
- `network_factory` must create new modules each call, not reuse a global module instance across processes.
- Start with small `num_actors`, conservative replay sizes, and `local_mt` while debugging shapes/imports.
- If actor variables appear stale, inspect distributed constructor `variable_update_period` and variable-client behavior.

## Saving, Checkpointing, And Variable Syncing

Acme TF savers live in `acme.tf.savers`.

| API | Use |
| --- | --- |
| `TFSaveable.state()` | Interface for objects that expose TensorFlow checkpointable state. |
| `Checkpointer(objects_to_save, directory=..., subdirectory='...', time_delta_minutes=..., enable_checkpointing=True, add_uid=False, max_to_keep=...)` | Saves TensorFlow checkpoints that require rebuilding the same objects before restore. |
| `Checkpointer.save(force=False)` / `restore()` | Periodic or forced save and restore. |
| `Snapshotter(objects_to_save, directory=..., time_delta_minutes=..., snapshot_ttl_seconds=...)` | Exports self-contained SavedModel snapshots for Sonnet/TF modules. |
| `Snapshotter.save(force=False)` | Periodic or forced snapshot. |
| `CheckpointingRunner(wrapped, key='...', time_delta_minutes=..., **kwargs)` | Wraps an Acme worker and saves it through a `Checkpointer`. |
| `SaveableAdapter(object_to_save)` | Adapts an Acme `core.Saveable` to TensorFlow checkpoint state. |
| `VariableClient(client, variables, update_period)` | Pulls variables from a variable source, with `update(wait=False)` and `update_and_wait()`. |

Patterns:

```python
from acme.tf import savers as tf2_savers

checkpointer = tf2_savers.Checkpointer(
    objects_to_save={'policy': policy_network},
    directory='checkpoints',
    subdirectory='learner',
)
snapshotter = tf2_savers.Snapshotter(
    objects_to_save={'policy': policy_network},
    directory='snapshots',
)
checkpointer.save(force=True)
snapshotter.save(force=True)
```

Guidance:

- Use checkpoints for preemption/restart of training state; recreate the same object graph before restore.
- Use snapshots for self-contained exported modules when the module has a traceable `__call__` signature.
- Snapshotter supports Sonnet/TF modules best after variables are created; run a representative call or `create_variables` first.
- For recurrent modules, ensure `initial_state` is traceable; Acme recurrent wrappers include saver-specific handling.
- Learners often create both a `Checkpointer` and a `Snapshotter` internally when `checkpoint=True`.

## TF Losses

Acme TF losses live under `acme.tf.losses`.

| Loss/API | Use |
| --- | --- |
| `losses.categorical(q_tm1, r_t, d_t, q_t, ...)` | Distributional categorical TD loss. |
| `losses.l2_project(...)` and `multiaxis_l2_project(...)` | Categorical support projection for distributional RL. |
| `losses.dpg(q_max, dqda_clipping=None, clip_norm=False)` | Deterministic policy gradient loss. |
| `losses.huber(inputs, quadratic_linear_boundary)` | Huber regression loss. |
| `losses.MPO(...)` | Sonnet module implementing MPO loss with KL/temperature constraints. |
| `losses.MultiObjectiveMPO(...)` | Sonnet module implementing multi-objective MPO constraints. |
| `losses.NonUniformQuantileRegression(...)` | Quantile regression support for IQN-like learners. |
| `losses.transformed_n_step_loss(...)` | R2D2 transformed n-step sequence loss. |

When adapting a learner, preserve the expected tensor ranks from the existing learner: actor-critic losses usually expect batched tensors; recurrent losses expect leading time/batch axes; distributional losses expect matching support/value dimensions.

## Eager Shape Validation Case

For a hard debugging case, validate shapes before restoring `@tf.function`:

```python
sample_observation = tf.nest.map_structure(
    lambda spec: tf.zeros((2,) + tuple(spec.shape), spec.dtype),
    environment_spec.observations,
)
sample_action = tf.zeros((2,) + tuple(environment_spec.actions.shape), environment_spec.actions.dtype)

policy_output = policy_network(sample_observation)
critic_output = critic_network(sample_observation, sample_action)
print(tf.nest.map_structure(lambda x: (x.shape, x.dtype), policy_output))
print(tf.nest.map_structure(lambda x: (getattr(x, 'shape', None), getattr(x, 'dtype', None)), critic_output))
```

If this fails in eager mode, fix the network contract before investigating graph-mode or Launchpad behavior.
