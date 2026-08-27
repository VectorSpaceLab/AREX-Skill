# Torch workflow and API

This reference is distilled from the 2.1.0 package metadata, Torch source, API
RST, the Pendulum PPO example, and Torch tests. It is written so a researcher
can compose a small public workflow without reopening the checkout.

## Install and import

The package declares `gymnasium`, `packaging`, `tensorboard`, and `tqdm` as
base dependencies and exposes PyTorch through the optional `torch` extra:

```bash
python -m pip install "skrl[torch]"
```

The public imports used by a standard Torch workflow are:

```python
from skrl.agents.torch.ppo import PPO, PPO_CFG
from skrl.memories.torch import RandomMemory
from skrl.models.torch import DeterministicMixin, GaussianMixin, Model
from skrl.trainers.torch import SequentialTrainer
```

`wandb` is imported only when `ExperimentCfg.wandb=True`; install and
configure it separately before enabling that flag. JAX, Warp, and environment-
specific integrations are optional boundaries, not prerequisites for this
single-agent Torch route.

Run the bundled component check before a real environment loop:

```bash
python scripts/torch_ppo_components.py --help
python scripts/torch_ppo_components.py --device cpu
```

The check creates a Gymnasium Pendulum space, two small public model
components, a four-step `RandomMemory`, a PPO config, and a PPO agent. It does
not train, create a trainer, write checkpoints, create TensorBoard files, or
write a run directory.

## Standard composition order

1. **Get spaces from the environment route.** `observation_space`,
   `state_space` (possibly `None`), and `action_space` are passed to every
   model and to the agent. The environment's Torch wrapper also supplies a
   compatible `device`; do not independently guess flattened dimensions.
2. **Choose model classes.** In multiple inheritance, put the mixin before
   `Model`, call `Model.__init__` first, then the mixin initializer, and
   implement only `compute`. The model's `compute` receives a dictionary with
   `observations`, optionally `states` and `taken_actions`, and returns
   `(tensor, outputs)`.
3. **Allocate memory.** `RandomMemory(memory_size=..., num_envs=..., device=...)`
   is an empty circular buffer. The agent creates its required tensors during
   `agent.init`; do not pre-create agent-owned names with incompatible sizes or
   dtypes.
4. **Create the exact model dictionary.** Required roles are in the algorithm
   table below. A policy-only evaluation instance may omit training-only roles,
   but a training instance must provide every role used by the algorithm.
5. **Configure the agent.** Use a dataclass (`PPO_CFG()`, etc.) or a config
   dictionary. Pass spaces, `device`, `models`, `memory`, and `cfg` to the
   algorithm constructor. `cfg.expand()` and nested `ExperimentCfg` handling
   happen in the base agent.
6. **Create a trainer.** `SequentialTrainer(cfg={"timesteps": ...,
   "headless": ...}, env=wrapped_env, agents=agent)` initializes the agent.
   Call `trainer.train()` or `trainer.eval()`, not the agent's internal
   `update()` directly.

Minimal shape of a real PPO composition:

```python
memory = RandomMemory(memory_size=rollouts, num_envs=env.num_envs,
                      device=env.device)
models = {
    "policy": Policy(env.observation_space, env.state_space,
                     env.action_space, env.device),
    "value": Value(env.observation_space, env.state_space,
                   env.action_space, env.device),
}
cfg = PPO_CFG()
cfg.rollouts = rollouts
cfg.mini_batches = 1                 # choose a divisor of the collected batch
cfg.experiment.write_interval = 0    # use for a no-write probe
cfg.experiment.checkpoint_interval = 0
agent = PPO(models=models, memory=memory, cfg=cfg,
            observation_space=env.observation_space,
            state_space=env.state_space, action_space=env.action_space,
            device=env.device)
trainer = SequentialTrainer(env=env, agents=agent,
                            cfg={"timesteps": 100_000, "headless": True})
```

For PPO/A2C/RPO/TRPO, `rollouts` counts interaction steps before an update;
with `num_envs > 1`, the memory contains `rollouts * num_envs` samples. The
reference example sets `memory_size == cfg.rollouts`. `mini_batches` must be
chosen so the resulting split is useful and not larger than the collected
batch. Off-policy agents use `batch_size`, `gradient_steps`,
`learning_starts`, and a replay-sized memory instead of a rollout alignment.

## Public signatures and controls

Verified public signatures at 2.1.0 include:

| Component | Constructor shape | Important behavior |
|---|---|---|
| `Model` | keyword-only spaces and optional `device` | Stores computed space sizes and resolves the device with `config.torch.parse_device` |
| `PPO` (same common shape for the named agents) | `models`, optional `memory`, spaces, `device`, `cfg` | Agent creates optimizers/preprocessors and agent-owned memory tensors in `init` |
| `PPO_CFG` | dataclass with `experiment`, `rollouts`, epochs, batches, preprocessing, clipping, KL, AMP fields | Learning-rate and scheduler values may be per-role tuples where documented |
| `ExperimentCfg` | `directory`, `experiment_name`, intervals, `store_separately`, `wandb`, `wandb_kwargs` | Defaults to `runs/<timestamp>_<agent>` only if a write/checkpoint operation is enabled |
| `RandomMemory` | keyword-only `memory_size`, `num_envs`, `device`, export options, `replacement` | Circular storage; no tensors exist until an agent creates them or the caller calls `create_tensor` |
| `SequentialTrainer` | `env`, `agents`, optional `scopes`, `cfg` | Owns the normal train/eval interaction loop |
| `StepTrainer` | same base constructor | `train()`/`eval()` perform one iteration and return environment outputs |
| `ParallelTrainer` | same base constructor | Uses spawned processes for simultaneous-agent operation; test picklability and shared-memory constraints first |

`AgentCfg.experiment` is a nested `ExperimentCfg`. `write_interval` and
`checkpoint_interval` accept an integer or `"auto"`; non-positive values
disable the respective operation. With `"auto"`, the agent derives TensorBoard
writes from roughly 100 samples and checkpoints from roughly 10 samples over
the trainer's `timesteps`; small smoke runs can derive interval zero, so use
explicit positive intervals for deterministic production cadence.

## Device behavior

`config.torch.parse_device(device, validate=True)` accepts `None`, a string,
or a `torch.device`. It tries the requested device by allocating a one-element
tensor; invalid or unavailable requests log a warning and fall back to the
available default (`cuda:0` when available, otherwise `cpu`). The prepared
2.1.0 facts report Torch 2.13.0+cpu, so `parse_device(None)` and invalid-device
fallback resolve to CPU in that environment. `config.torch.device` is a
separate mutable default-device property; set it deliberately rather than
using it as proof that CUDA exists.

Pass one resolved device consistently to models, memory, and the agent. A CPU
import or CPU component check does not validate CUDA kernels, CUDA memory,
NCCL/distributed setup, MPS, or any vendor backend. Distributed Torch is
activated from `WORLD_SIZE > 1` and initializes the process group; only launch
that mode under an appropriate distributed launcher and backend.

## Model construction rules

### Custom models

```python
class Policy(GaussianMixin, Model):
    def __init__(self, observation_space, state_space, action_space, device):
        Model.__init__(self, observation_space=observation_space,
                       state_space=state_space, action_space=action_space,
                       device=device)
        GaussianMixin.__init__(self, clip_actions=True)
        self.net = nn.Sequential(...)
        self.log_std_parameter = nn.Parameter(torch.zeros(self.num_actions))

    def compute(self, inputs, role):
        return self.net(inputs["observations"]), {
            "log_std": self.log_std_parameter
        }
```

For `DeterministicMixin`, return the value, action, or critic scalar and an
outputs dictionary. `GaussianMixin` requires `outputs["log_std"]`; its default
log-probability reduction is `sum`, and it supports action/mean clipping and
log-standard-deviation bounds. `CategoricalMixin` interprets `compute` output
as logits by default (`unnormalized_log_prob=True`); if that flag is false,
return valid non-negative probabilities. `MultiCategoricalMixin` splits the
last dimension according to `MultiDiscrete.nvec` and reduces component
log-probabilities by `sum` by default. `MultivariateGaussianMixin` expects a
mean vector plus `log_std` and constructs a diagonal multivariate normal.
`TabularMixin` returns the table-driven action/value and exposes `tables()`.

The docs require the mixin before `Model` in the class definition and the
`Model` constructor before every mixin constructor. A shared model must call
all mixin constructors, override `act` to dispatch by `role`, and reuse the
same model instance for all dictionary keys. Role strings such as `policy`,
`value`, `critic_1`, and `critic_2` are the discriminator for shared models.
Single-forward-pass sharing is only safe when the algorithm's value pass
follows the policy pass (the docs call out PPO as the motivating case).

### Model instantiators

For architecture-generated models, the public Torch helpers are:

- `deterministic_model(..., network=[], output="", return_source=False)`
- `gaussian_model(..., initial_log_std=0, fixed_log_std=False, network=[],
  output="", return_source=False)`
- `categorical_model(...)`
- `multicategorical_model(...)`
- `multivariate_gaussian_model(...)`
- `tabular_model(...)`
- `shared_model(..., structure, roles, parameters,
  single_forward_pass=True, return_source=False)`

These helpers return a model unless `return_source=True`, in which case they
return generated source. Prefer a small explicit `network` and inspect the
resulting model before training. Lazy/generated models may need
`model.init_state_dict(...)` before relying on their parameters; this is
especially relevant to custom lazy layers and shared architectures.

## Evaluation, logging, and safe resume

- For evaluation, instantiate an architecture-equivalent agent, set
  `cfg.experiment.write_interval = 0` and `checkpoint_interval = 0`, call
  `agent.load(path)` before `trainer.eval()`, and use
  `stochastic_evaluation=False` when deterministic mean actions are wanted.
- `agent.load(path)` is recommended over loading only a model because an agent
  checkpoint can include models, optimizers, schedulers, preprocessors, and
  other registered modules. The destination device is determined by the
  constructor. Model or agent structure must match the saved state dict;
  changed layer sizes, roles, action dimensions, or missing modules are not a
  safe resume.
- During training, checkpoints are written below the experiment directory's
  `checkpoints/` directory. `store_separately=True` writes each registered
  module separately; otherwise it writes an `agent_<timestep>.pt` dictionary.
  Best modules are tracked from mean total reward and use `best_agent.pt` or
  separate `best_<name>.pt` files.
- TensorBoard is enabled when the resolved write interval is positive; launch
  `tensorboard --logdir <runs-directory>` outside the training process.
  `wandb=True` dynamically imports `wandb`, syncs TensorBoard by default, and
  adds agent/trainer/model configuration to its setup.
- A memory's optional export (`pt`, `npz`, or `csv`) is distinct from an agent
  checkpoint and occurs when the circular buffer fills. Avoid enabling export
  in a bounded smoke.
