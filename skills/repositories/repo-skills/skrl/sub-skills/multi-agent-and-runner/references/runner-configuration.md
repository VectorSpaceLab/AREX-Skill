# Runner configuration

`Runner` is a convenience layer around public environment wrappers, model
instantiators, memory classes, agent configuration, and a trainer. It hides
construction details, so use it for a declarative workflow only when the
configuration is trusted and the generated components match the environment.
For code that needs custom model logic or a non-supported trainer, construct
components directly.

## Required shape

Use the framework-specific import and pass a **wrapped** environment:

```python
from skrl.utils.runner.torch import Runner
from skrl.envs.wrappers.torch import wrap_env

env = wrap_env(original_env, wrapper="pettingzoo")
cfg = Runner.load_cfg_from_yaml("config.yaml")
runner = Runner(env, cfg)
runner.run("train")  # or "eval"
```

Use the matching JAX or Warp wrapper/Runner imports for those frameworks.
`Runner(env, cfg, verbose=False)` requires `env` to be the public
`Wrapper` or `MultiAgentEnvWrapper` for that framework. It detects a
multi-agent wrapper and obtains `possible_agents`, per-agent spaces, and
`num_envs` from it. Passing the original PettingZoo/Gym object skips the
normalized skrl interface and commonly fails before model construction.

The top-level configuration has this shape:

```yaml
seed: 42
models:
  separate: true
  policy:
    class: GaussianMixin
    network:
      - name: net
        input: OBSERVATIONS
        layers: [64, 64]
        activations: elu
    output: ACTIONS
  value:
    class: DeterministicMixin
    network:
      - name: net
        input: STATES
        layers: [64, 64]
        activations: elu
    output: ONE
memory:
  class: RandomMemory
  memory_size: -1
agent:
  class: MAPPO
  rollouts: 16
  learning_epochs: 8
  mini_batches: 2
  observation_preprocessor: null
  state_preprocessor: null
  value_preprocessor: null
  experiment:
    directory: runs/mappo
    experiment_name: ""
    write_interval: auto
    checkpoint_interval: auto
trainer:
  class: SequentialTrainer
  timesteps: 100000
  headless: true
```

For IPPO, change `agent.class` to `IPPO` and make the value network consume
local observations unless an explicit state-based independent critic is
intended. For MAPPO, a value network with `input: STATES` requires the wrapper
to expose a non-`None` state space and state values. This YAML is a shape
illustration, not a promise that an arbitrary action/observation space matches
these Gaussian model classes.

Required sections and errors are straightforward:

- no `agent` -> `ValueError` that `agent` is not defined;
- no `agent.class` -> `ValueError` that `agent.class` is not defined;
- no `models` -> `ValueError` that `models` is not defined;
- no `memory` or `memory.class` -> corresponding `ValueError` (agent creation
  path, including evaluation configurations that should omit memory only when
  constructing directly);
- no `trainer` or `trainer.class` -> corresponding `ValueError`;
- missing `models.<role>.class` -> `ValueError` naming that role;
- unknown component string -> `ValueError` that the component is unsupported.

When `memory.memory_size < 0`, Runner replaces it with `agent.rollouts` and
creates one memory object per possible agent. The generated multi-agent agent
receives the full nested `models`, `memories`, observation/state/action space
mappings, and possible-agent list. A Runner config is therefore not a way to
provide one policy/value model dictionary for all possible agents.

## Component strings

Strings are case-insensitive and are resolved by each framework's
`Runner._component` table. Relevant Torch and JAX names include:

| YAML field | Torch/JAX component strings |
|---|---|
| policy model | `GaussianMixin`, `CategoricalMixin`, `MultiCategoricalMixin`; Torch also `MultivariateGaussianMixin` |
| value model | `DeterministicMixin` |
| role-shared Torch model | `Shared` |
| memory | `RandomMemory` |
| multi-agent algorithm | `IPPO`, `IPPO_CFG`, `MAPPO`, `MAPPO_CFG` |
| declarative trainer | `SequentialTrainer`; its internal config component is resolved as `SequentialTrainerCfg` (`sequentialtrainer_cfg`) |

The exact config-class mapping is framework code, not a general import-by-name
mechanism. The supported trainer mapping in these Runner implementations is
`SequentialTrainer`/`SequentialTrainerCfg`; `ParallelTrainer` and `StepTrainer`
are not Runner component entries. Construct those trainers directly with a
validated agent and environment when needed. Warp's component map contains
single-agent DDPG/PPO/SAC, `RandomMemory`, model instantiators, and
`SequentialTrainer`; it contains no IPPO or MAPPO.

Runner model construction loops through every `possible_agents` ID. With
`models.separate: true` (the safe/default mode), it instantiates each role
independently using that ID's observation/state/action spaces. `class` is
removed from each role before its model-instantiator call. With Torch
`models.separate: false`, exactly two role entries are required; Runner builds
one Torch `Shared` model and aliases it under both roles for each agent ID.
This shares policy/value parameters for an agent, not parameters across all
agent IDs. JAX does not support this shared branch: if `models.separate` is
present, JAX Runner forces it to `true`; otherwise it defaults to separate
models. Warp can build shared policy/value roles for its single-agent models,
but not multi-agent IPPO/MAPPO.

The Runner's `_process_cfg` also converts selected string values to Python
objects and expression fields to callables. It handles `learning_rate_scheduler`,
`observation_preprocessor`, `state_preprocessor`, `value_preprocessor`,
noise fields, and related direct-evaluation strings; it turns
`exploration_scheduler` into a lambda expression and applies
`rewards_shaper_scale`. Since this uses evaluation of configuration text, do
not load or execute untrusted YAML. Prefer explicit Python construction when
the config is supplied by another user or system.

## Compatibility migration

Before generation, all three Runner implementations apply the same compatibility
pass to the `agent` dictionary:

| Old key/shape | New behavior | How to write new configs |
|---|---|---|
| `lambda` | copied to `gae_lambda`, old key removed, warning logged | `gae_lambda` |
| `clip_predicted_values` | removed; `value_clip` becomes its existing value when true, or `0.0` when false; warning logged | set `value_clip > 0` to clip, otherwise `0.0` |
| `state_preprocessor` without `observation_preprocessor` | moved to `observation_preprocessor`, kwargs moved too, old state keys removed, warning logged | define both explicitly; set `observation_preprocessor: null` if a state preprocessor is intentionally used alone |
| `shared_state_preprocessor` | moved to `state_preprocessor` with kwargs, old key removed, warning logged | `state_preprocessor` |

The migration mutates a deep copy, so the caller's original config is not the
object being rewritten by the compatibility pass. It does not fix arbitrary
misspellings, incomplete per-agent mappings, invalid model expressions, or a
wrong centralized-state design.

## YAML loading and parser checks

`Runner.load_cfg_from_yaml(path)` imports PyYAML lazily and calls
`yaml.safe_load`. PyYAML is optional:

- if it cannot be imported, Runner logs an install hint and returns `{}`;
- if the file cannot be opened or parsed, Runner logs a loading error and
  returns `{}`;
- valid YAML returns its loaded object (normally a dictionary).

An empty result is not a valid Runner configuration. Check that the returned
value is a non-empty mapping before constructing a Runner and report the
original parse/import error rather than debugging `agent.class` downstream.
A safe parser-only check can use a temporary, trusted YAML file and should not
call `runner.run` or instantiate a user environment.

## Checkpoints and logging

The agent's `experiment` configuration controls artifact placement:

- `directory` defaults to a `runs` directory under the current working
  directory when empty;
- `experiment_name` defaults to a timestamp plus agent class when empty;
- `write_interval: auto` resolves to approximately `timesteps / 100`;
- `checkpoint_interval: auto` resolves to approximately `timesteps / 10`;
- an interval `<= 0` disables that output;
- `store_separately: true` writes each per-agent module separately; false
  writes one nested whole-agent artifact;
- `wandb: true` adds Weights & Biases setup and is an optional dependency.

Multi-agent artifacts preserve the outer agent ID and inner role/module names.
Torch uses `.pt` files and a whole-agent mapping; JAX serializes module bytes
in `.pickle` files. Use the matching framework's `agent.load(path)` and
recreate the same possible-agent IDs, role keys, model architecture, and
optimizer/preprocessor arrangement before loading. A checkpoint is not a
portable single-agent policy if it contains per-agent nested modules.

Runner returns `runner.agent` and `runner.trainer`; load a compatible
checkpoint after construction and before `run`. Do not infer success from a
created runs directory alone: validate the agent's model/role shape and the
checkpoint path, and keep evaluation writes disabled when a read-only probe is
intended.

## Distributed boundary

Distributed execution and trainer multiprocessing are separate concerns.

### Torch

Use the framework's documented `torchrun` launch path. skrl reads
`LOCAL_RANK`, `RANK`, and `WORLD_SIZE` through `config.torch.local_rank`,
`config.torch.rank`, and `config.torch.world_size`. When `WORLD_SIZE > 1`,
skrl initializes the Torch process group and uses the local device. IPPO/MAPPO
broadcast model parameters at construction and reduce gradients during
updates. Nonzero ranks disable TensorBoard/checkpoint intervals to avoid
duplicate artifacts. Verify that every rank sees the same possible-agent order,
model role structure, and compatible environment shard before launching.

### JAX

The JAX launcher is invoked as:

```bash
python -m skrl.utils.distributed.jax \
  --nnodes 1 --nproc-per-node 2 --node-rank 0 \
  --coordinator-address 127.0.0.1:5000 \
  train_script.py --your-script-arg value
```

The launcher sets `JAX_LOCAL_RANK`, `JAX_RANK`, `JAX_WORLD_SIZE`,
`JAX_COORDINATOR_ADDR`, and `JAX_COORDINATOR_PORT`. skrl exposes these through
`config.jax.local_rank`, `rank`, `world_size`, and `coordinator_address`; a
world size above one initializes JAX distributed and forces each process onto
its local device. The JAX multi-agent update reduces gradients and, for a KL
adaptive scheduler, reduces the KL statistic. Nonzero ranks suppress repeated
logging/checkpoint output. Coordinator address/port, process count, and
reachable devices must be correct on every host.

### Do not conflate modes

`ParallelTrainer` starts local Torch worker processes for simultaneous agent
instances and has shared-memory/pickling/GPU-overhead constraints. It is not a
replacement for Torch distributed or the JAX launcher. Warp Runner has no
corresponding IPPO/MAPPO distributed path. Keep distributed validation to
imports, rank/config inspection, and launcher `--help` unless the caller has
explicitly approved a bounded multi-process run.
