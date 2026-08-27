# JAX workflow and API contract

This is a public-package operating guide for skrl 2.1.0. API names below are
anchored to the public `skrl.*.jax` modules and the installed 2.1.0 signatures
checked for this branch. The maintained JAX Gymnasium Pendulum PPO example is
the construction-order anchor; it is intentionally not a training recipe for
this skill.

## Installation and runtime selection

The JAX extra declares `jax`, `jaxlib`, `flax`, and `optax` (with the package's
Python floor). Follow this order:

```bash
# Choose the CPU or accelerator-compatible JAX/JAXLIB build first.
# Use the current JAX installation selector for accelerator-specific commands.
python -m pip install <chosen-jax-runtime>
python -m pip install 'skrl[jax]'
```

Do not replace `<chosen-jax-runtime>` with a generic `pip install jax` when GPU
execution is required: the default JAX installation is commonly CPU-only. The
`jaxlib` wheel is the runtime/backend choice; a machine having an NVIDIA GPU is
not evidence that the installed JAX process can use CUDA. Check both:

```python
import jax
print(jax.default_backend())
print(jax.devices())
```

The package's `config.jax.parse_device(device)` accepts `None`, a JAX device,
or PyTorch-like strings such as `"cpu"` and `"cuda:0"`. It attempts the named
backend/index and returns `jax.devices()[0]` after an invalid/unavailable
specification. Therefore a CPU-only installation can log a warning for
`"cuda:0"` and continue on its first CPU device. This is a fallback observation,
not a CUDA compatibility guarantee. In a configured distributed run,
`config.jax.parse_device` prefers the device local to the current process.

## NumPy versus JAX arrays

The maintained examples assign `config.jax.backend = "numpy"` (or `"jax"`). In
this 2.1.0 source, that attribute is not declared as a `JAX` configuration
property and the space helper does not read it. Treat it as an example-level
compatibility marker, not a global backend switch. The explicit public choice
is `skrl.utils.spaces.jax.sample_space(..., backend="numpy"|"native")`:

- `backend="numpy"` returns NumPy samples.
- `backend="native"` returns JAX arrays placed on the selected device.
- invalid values raise `ValueError`.

`Model.init_state_dict` deliberately calls `sample_space` with
`backend="native"`, so changing an example marker cannot make model parameters
NumPy-backed. Use `jax.numpy`/JAX arrays for model inputs and agent execution;
convert at the environment boundary through the JAX wrapper. This distinction
is why a successful NumPy sampling check is not a successful JAX model check.

## PRNG, device, and seed

`config.jax.key` is a JAX PRNG key on the configured device. The public setter
accepts an integer, a NumPy `uint32` key, or a JAX key; assigning an integer
creates the two-word PRNG representation. `skrl.utils.set_seed(seed)` is the
normal reproducibility entry point and updates framework keys. For an isolated
model initialization, pass `key=jax.random.PRNGKey(seed)` to
`init_state_dict`; otherwise the method uses `config.jax.key`.

The stochastic mixins keep a key and fold in an incrementing counter for each
`act` call. Do not assume two independent policies share a stream just because
they were initialized at the same time; use explicit keys for controlled
fixtures and separate model instances for separate policies. Device placement
is established by `config.jax.parse_device` and `jax.default_device` around
initialization/updates. Keep environment arrays, memory tensors, model
parameters, and preprocessors on the same JAX device unless a deliberate
transfer is part of the environment adapter.

## Flax model contract

JAX models are Flax modules with an explicit parameter/state container rather
than Torch-style mutable `Parameter` objects. The public base is
`skrl.models.jax.Model` and the public helper mixins are:

| Model kind | Class | Model output contract | Main options |
|---|---|---|---|
| Continuous deterministic | `DeterministicMixin` | action/value plus extra dict | `clip_actions` |
| Continuous stochastic | `GaussianMixin` | sampled action plus `log_prob`, `log_std`, `mean_actions`, `stddev` | action/mean clipping, log-std bounds, `reduction` |
| Discrete stochastic | `CategoricalMixin` | integer action plus `log_prob`, `net_output`, `stddev` placeholder | `unnormalized_log_prob` |
| Multi-discrete stochastic | `MultiCategoricalMixin` | one action per categorical component plus reduced or unreduced log-probability | `unnormalized_log_prob`, `reduction` |

Always inherit in this order:

```python
class Policy(GaussianMixin, Model):
    ...
```

Call the base constructors in the same order (the `Model` constructor first),
then define `__call__` with Flax `@nn.compact` or `setup`. All extra constructor
arguments need defaults because Flax may instantiate modules during variable
initialization. A model's callable receives a dictionary with common keys
`"observations"`, `"states"`, and, for critics, `"taken_actions"`, plus the
agent role. Return a tuple; the first value must have the shape expected by the
agent and the second is the auxiliary output dictionary.

Typical implementations:

```python
class Policy(GaussianMixin, Model):
    def __init__(self, observation_space, state_space, action_space, device,
                 clip_actions=False, clip_log_std=True,
                 min_log_std=-20, max_log_std=2, reduction="sum", **kwargs):
        Model.__init__(self, observation_space=observation_space,
                       state_space=state_space, action_space=action_space,
                       device=device, **kwargs)
        GaussianMixin.__init__(self, clip_actions=clip_actions,
                               clip_log_std=clip_log_std,
                               min_log_std=min_log_std,
                               max_log_std=max_log_std,
                               reduction=reduction)

    @nn.compact
    def __call__(self, inputs, role):
        x = nn.relu(nn.Dense(64)(inputs["observations"]))
        return nn.Dense(self.num_actions)(x), {"log_std": self.param(
            "log_std", lambda _: jnp.zeros(self.num_actions))}
```

A value or critic uses `DeterministicMixin` and normally returns shape
`(batch, 1)`. A critic that uses actions must concatenate
`inputs["observations"]` and `inputs["taken_actions"]` (or use the equivalent
model-instantiator input expression). The action-space limits are applied only
when the selected clipping option is enabled; a bounded policy's final network
activation alone is not a substitute for understanding the mixin's clipping
settings.

### State dictionary initialization is mandatory

After constructing every model, run:

```python
for role, model in models.items():
    model.init_state_dict(role=role)
```

The public signature is `init_state_dict(inputs={}, *, role="", key=None)`. With
empty inputs it samples observation/state/action spaces using native JAX arrays,
uses `config.jax.key` if no key is supplied, initializes Flax variables on the
model device, and stores a `StateDict` containing `apply_fn` and `params`.
Without this call, `.act()` has no `state_dict` and fails with an attribute
error. With an incorrect role or missing input keys, initialization can fail
inside the model or later under a JIT trace; use the exact agent model key.

`state_dict.params` is a PyTree. Parameter updates replace the immutable Flax
state container; do not write Torch-style in-place `.grad` or `.to()` code.
`init_parameters`, `init_weights`, and `init_biases` operate on an already
initialized state dictionary. `model.save/load` is a model-only serialization
boundary; prefer agent checkpoints when optimizers/preprocessors are part of a
run.

## Memory, resources, agent, trainer

`RandomMemory(memory_size, num_envs=1, device=None, replacement=False)` is the
JAX random-sampling memory. It is initially an empty shell. The agent's
`init()` creates algorithm-specific tensors; PPO adds observations, states,
actions, rewards, termination flags, log probability, values, returns, and
advantages. In an ordinary trainer construction, `SequentialTrainer` calls
`agent.init(...)`. If the loop is custom, call `agent.init(trainer_cfg=...)`
before using memory tensors.

Useful JAX resources include:

| Resource | Public API | Use |
|---|---|---|
| Optimizer | `skrl.resources.optimizers.jax.Adam` | Optax Adam with optional global gradient clipping; returns an immutable optimizer object from `.step(...)`. |
| Scheduler | `skrl.resources.schedulers.jax.KLAdaptiveLR` | Optax-style callable schedule; pass the class and kwargs in agent config. |
| Preprocessor | `skrl.resources.preprocessors.jax.RunningStandardScaler` | JAX running normalization; configure `size` with a space or integer and `device`. |
| Exploration noise | `GaussianNoise`, `OrnsteinUhlenbeckNoise` | Primarily deterministic off-policy actor exploration; select the JAX class in the algorithm config. |

`PPO` and the other JAX agents accept keyword-only `models`, optional
`memory`, spaces, `device`, and a `*_CFG` instance or dictionary. Use the exact
model dictionary keys in the algorithm table. A configuration object is safer
than an unvalidated ad-hoc dictionary because nested `experiment` settings are
explicit; if using a dictionary, use the installed dataclass field names.

`SequentialTrainer(env=..., agents=..., cfg=...)` owns the ordinary train/eval
loop and calls the agent initialization. `StepTrainer` has the same component
contract but exposes one bounded `train(timestep=..., timesteps=...)` or
`eval(...)` iteration and returns environment outputs. Both expect a skrl JAX
wrapper, not a raw Gymnasium environment; route wrapping to the environment
skill. Trainer defaults include `timesteps`, `headless`, `render_interval`,
`disable_progressbar`, `close_environment_at_exit`, and
`stochastic_evaluation`.

## Logging, checkpoints, and evaluation boundaries

The nested agent experiment configuration controls output:

- `experiment.directory` and `experiment.experiment_name` identify the run.
- `write_interval <= 0` disables TensorBoard scalar writing; `"auto"` targets
  about 100 writes across the requested timesteps.
- `checkpoint_interval <= 0` disables checkpoints; `"auto"` targets about 10
  checkpoints across the requested timesteps.
- `store_separately=True` writes each checkpoint module separately; the default
  stores the agent modules together.
- `wandb=True` is an optional external logging integration and is outside a
  no-network smoke.

`agent.save(path)` serializes all registered checkpoint modules (models,
optimizers, and configured preprocessors); `agent.load(path)` restores matching
modules and warns for unknown module names. Reconstruct the same model
architecture, model keys, and component structure before loading. A missing
checkpoint path is an application error, not a signal to initialize random
weights silently.

For evaluation, call `trainer.eval()` (or `StepTrainer.eval(...)`) after loading
an agent checkpoint. The sequential JAX trainer uses stochastic actions only
when `stochastic_evaluation=True`; otherwise a stochastic policy's
`mean_actions` is used when available. Do not mix an evaluation-only config
(`write_interval=0`, `checkpoint_interval=0`) with a claim that no environment
steps occurred: it suppresses artifacts, not interaction. The bundled smoke
avoids both train and eval loops.

## Evidence anchors

- `[Install]` public skrl installation guidance and the `skrl[jax]` dependency
  declaration.
- `[Config]` `skrl.config.jax` public properties `device`, `parse_device`,
  `key`, and distributed rank fields, plus the public JAX configuration test.
- `[Model]` `skrl.models.jax.Model` and the four public mixin modules.
- `[Spaces]` `skrl.utils.spaces.jax.sample_space` explicit `numpy`/`native`
  backend argument.
- `[PPO]` `skrl.agents.jax.ppo.PPO`, `PPO_CFG`, and the public PPO agent/model
  documentation.
- `[Memory]` `skrl.memories.jax.Memory` and `RandomMemory`.
- `[Resources]` public JAX Adam, KLAdaptiveLR, RunningStandardScaler, and
  noise APIs.
- `[Trainer]` `skrl.trainers.jax.SequentialTrainer`, `StepTrainer`, and their
  trainer configuration.
- `[Example]` maintained JAX Gymnasium Pendulum PPO construction sequence.
