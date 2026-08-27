# Warp algorithm and component selection

Choose the algorithm from the learning/data regime first, then make model role
names and tensor shapes agree with that choice. All examples below are
single-agent and assume an already wrapped Warp environment with `device` set
to the same resolved Warp device for every component.

## PPO: on-policy rollout

Use PPO when updates consume a fresh rollout and the policy is stochastic for a
continuous action space. The standard Warp PPO arrangement is:

```python
from skrl.agents.warp.ppo import PPO, PPO_CFG
from skrl.memories.warp import RandomMemory
from skrl.resources.preprocessors.warp import RunningStandardScaler
from skrl.resources.schedulers.warp import KLAdaptiveLR

models = {"policy": policy, "value": value}
cfg = PPO_CFG(
    rollouts=1024,
    learning_epochs=10,
    mini_batches=32,
    observation_preprocessor=RunningStandardScaler,
    observation_preprocessor_kwargs={"size": env.observation_space, "device": device},
    value_preprocessor=RunningStandardScaler,
    value_preprocessor_kwargs={"size": 1, "device": device},
    learning_rate_scheduler=KLAdaptiveLR,
    learning_rate_scheduler_kwargs={"kl_threshold": 0.008},
    experiment={"write_interval": 0, "checkpoint_interval": 0},
)
memory = RandomMemory(memory_size=cfg.rollouts, num_envs=env.num_envs, device=device)
agent = PPO(
    models=models,
    memory=memory,
    cfg=cfg,
    observation_space=env.observation_space,
    state_space=env.state_space,
    action_space=env.action_space,
    device=device,
)
```

`PPO_CFG.expand()` turns a scalar learning rate and scheduler into two entries
(policy and value). `rollouts` should match the rollout memory capacity for the
usual configuration. `mini_batches` must be chosen consistently with the
available rollout samples. `time_limit_bootstrap` controls timeout handling;
do not change it without understanding how the wrapped environment marks
`terminated` and `truncated`.

Role requirements:

- `policy`: a stochastic `GaussianMixin` model for a continuous Box action
  space, or another supported mixin for the action space.
- `value`: a `DeterministicMixin` model returning one value per sample.
- The value model can consume observations or an optional privileged state;
  construct it against the matching `state_space` and input contract.
- A shared model can implement both roles, but it must dispatch by `role` and
  the same instance may be placed under both dictionary keys. Prefer separate
  models until a shared model has been tested.

The Gaussian model's `compute` returns mean actions and an output dictionary
containing `log_std`. The mixin produces sampled actions, log probabilities,
mean actions, and standard deviations. The model definition must inherit with
the mixin first:

```python
class Policy(GaussianMixin, Model):
    def __init__(self, observation_space, state_space, action_space, device):
        Model.__init__(
            self,
            observation_space=observation_space,
            state_space=state_space,
            action_space=action_space,
            device=device,
        )
        GaussianMixin.__init__(self, clip_actions=False, reduction="sum")
        self.net = nn.Sequential(...)
        self.log_std_parameter = nn.Parameter(wp.zeros(self.num_actions))
        self.__post_init__()

    def compute(self, inputs, role):
        return self.net(inputs["observations"]), {"log_std": self.log_std_parameter.data}
```

The ellipses are user-defined `warp_nn.nn` layers; the output must have
`num_actions` columns. The value model follows the same lifecycle with
`DeterministicMixin` first and returns a one-column output. Call
`__post_init__()` after defining Warp-NN modules/parameters. If using a lazy
model instantiator rather than an explicit class, call
`model.init_state_dict(role="policy")` (and the corresponding role for each
model) before the agent uses parameters.

## DDPG: off-policy deterministic actor-critic

Use DDPG for continuous bounded actions with replay and explicit exploration
noise. The required model dictionary is:

```python
models = {
    "policy": policy,
    "target_policy": target_policy,
    "critic": critic,
    "target_critic": target_critic,
}
```

The actor and target actor are deterministic models. The critic and target
critic return scalar values and consume observations/states plus actions. The
agent freezes target models and performs an initial hard copy from the live
models; later target updates use `polyak` averaging.

Use a replay capacity substantially larger than `batch_size`, and set
`learning_starts`/`random_timesteps` high enough to avoid updating from an
empty or uninformative buffer. DDPG warns when no exploration noise is
configured. A typical resource configuration is:

```python
from skrl.resources.noises.warp import GaussianNoise
from skrl.agents.warp.ddpg import DDPG_CFG

cfg = DDPG_CFG(
    batch_size=64,
    learning_starts=64,
    random_timesteps=64,
    exploration_noise=GaussianNoise,
    exploration_noise_kwargs={"mean": 0.0, "std": 0.1, "device": device},
    experiment={"write_interval": 0, "checkpoint_interval": 0},
)
```

`OrnsteinUhlenbeckNoise` is another Warp exploration resource. Its public
constructor accepts `theta`, `sigma`, `base_scale`, and `device`. The noise is
scaled/clipped against the bounded action space by DDPG. If the action space is
unbounded or not compatible with the expected limits, fix the environment/model
contract instead of relying on clipping.

`DDPG_CFG.expand()` expands a scalar learning rate/scheduler into actor and
critic entries. `gradient_steps`, `discount_factor`, `polyak`, preprocessors,
and optional reward shaping are algorithm controls, not trainer controls.

## SAC: off-policy stochastic actor with twin critics

Use SAC for continuous bounded actions when entropy-regularized stochastic
exploration and replay are desired. The required model dictionary is:

```python
models = {
    "policy": policy,
    "critic_1": critic_1,
    "critic_2": critic_2,
    "target_critic_1": target_critic_1,
    "target_critic_2": target_critic_2,
}
```

The policy is Gaussian and returns `log_prob`; both live critics and both
frozen target critics are deterministic scalar models consuming state/observation
and action. SAC computes a default target entropy from the action space when
`target_entropy` is `None`; set it explicitly when the task needs a different
entropy target. `learn_entropy` controls the entropy coefficient update and
`initial_entropy_value` seeds it.

`SAC_CFG.expand()` expands a scalar learning rate/scheduler into three entries:
policy, critic, and entropy coefficient. Keep `batch_size` below the available
replay size at the first update and set `learning_starts` accordingly.

## Model instantiators versus explicit classes

The public Warp model-instantiator helpers are useful for a compact network
specification:

- `deterministic_model(..., network=..., output="ACTIONS"|"ONE")`
- `gaussian_model(..., network=..., output="ACTIONS")`
- `shared_model(..., structure=..., roles=..., parameters=...)`

A network description names layers, an input expression such as
`"OBSERVATIONS"` or `"concatenate([OBSERVATIONS, ACTIONS])"`, and activations.
Critic input expressions must include the action tensor. Instantiators can
return source text when `return_source=True`, but production code normally uses
the returned model. They may create lazy parameters, so initialize each model:

```python
for role, model in models.items():
    model.init_state_dict(role=role)
```

Do not confuse model role keys with `role` passed into `compute`. Both must be
consistent. A model can be constructible yet still fail during `act` if its
output shape or role-specific input is wrong.

## Memory, preprocessing, and schedulers

`RandomMemory` stores circular buffers with shape conceptually
`(memory_size, num_envs, data_size)`. Its agent creates the named tensors during
`agent.init()`. For PPO, use the rollout count as capacity; for DDPG/SAC, use a
replay capacity and sample with `batch_size`. `replacement=False` samples at
most the currently valid number of entries; `replacement=True` guarantees the
requested batch size by allowing duplicates.

`RunningStandardScaler` accepts `size` and `device`; configure separate
observation/state/value preprocessors only when the model/agent contract needs
them. `KLAdaptiveLR` is exposed from `skrl.resources.schedulers.warp` as both
`KLAdaptiveLR` and `kl_adaptive`; pass its constructor options through
`learning_rate_scheduler_kwargs` and never supply an `optimizer` key (the agent
owns optimizer construction).

Set `experiment.write_interval=0` and `checkpoint_interval=0` for safe
construction checks. Enable logging/checkpointing only after choosing an
intentional output directory and validating the full architecture.

## Trainer boundary

For this single-agent branch, use `SequentialTrainer`:

```python
trainer = SequentialTrainer(
    env=env,
    agents=agent,
    cfg={
        "timesteps": 100_000,
        "headless": True,
        "disable_progressbar": False,
    },
)
trainer.train()  # or trainer.eval()
```

The Warp `SequentialTrainer` supports a single agent. Its simultaneous-agent
path raises `NotImplementedError`; do not present `scopes` as a multi-agent
solution. Route multi-agent and Runner configuration to the owning branches.
