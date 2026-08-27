# Warp workflow and API

This reference describes the public `skrl` 2.1.0 Warp surface. The package's
Warp extra declares `warp-lang>=1.12` and `warp-nn>=0.1`; the prepared
inspection evidence resolved `skrl 2.1.0`, `warp-lang 1.16.0`, and `warp-nn
0.3.1`. Pin versions in a reproducible project if a simulator or deployment
stack requires a narrower compatibility range.

## Install and initialize

For a PyPI installation, install the optional extra in the same environment as
the program:

```bash
python -m pip install "skrl[warp]==2.1.0"
```

For an editable checkout, the documented form is:

```bash
python -m pip install -e ".[warp]"
```

The extra supplies both `warp-lang` and `warp-nn`. Installing only `skrl` does
not supply either optional ML framework. A direct installation can be useful for
an explicitly managed Warp version, but it must still satisfy the package
minimums:

```bash
python -m pip install "warp-lang>=1.12" "warp-nn>=0.1"
```

A robust application startup order is:

```python
import warp as wp

wp.init()

from skrl import config
from skrl.envs.wrappers.warp import wrap_env
```

Importing `skrl` before `warp` can still work for ordinary package imports, but
explicit initialization makes the intended Warp runtime visible before device
selection and model construction. Do not place private inspection prefixes,
checkout paths, or local cache paths in a user-facing workflow.

Check the distribution and framework versions with standard package metadata or
`pip show`; check the runtime device with Warp itself. The version numbers above
are evidence for the prepared environment, not a promise that every CUDA or
simulator combination is compatible.

## Device selection and fallback

`skrl.config.warp.parse_device(device)` accepts `None`, a Warp device, or a
string such as `"cpu"` or `"cuda:0"`, and returns a Warp `Device`. The default
configuration starts from `cuda:0` and resolves to the first available default
Warp device. Invalid or unavailable strings are warned about and fall back to
that default; therefore an invalid CUDA request is **not** a reliable way to
ask for CPU.

Use an explicit CPU request when CPU is the selected verification target:

```python
from skrl import config

config.warp.device = "cpu"
device = config.warp.parse_device("cpu")
assert device == config.warp.device
```

Use an explicit CUDA request only after checking the target runtime:

```python
import warp as wp
from skrl import config

wp.init()
device = config.warp.parse_device("cuda:0")
```

All environment tensors, memories, models, resources, and agents in one
workflow should use the same resolved device. `config.warp.key` is an integer
PRNG key used by Warp resources/mixins; set it deliberately for reproducible
experiments, but do not treat a seed as a guarantee of cross-device bitwise
identity.

CPU support and CUDA support have different evidence requirements:

| Question | Safe package/API evidence | Requires extra runtime evidence |
| --- | --- | --- |
| Is the Warp extra importable? | Import `warp`, `warp_nn`, and selected skrl Warp modules. | None beyond the import environment. |
| Does `"cpu"` resolve? | `config.warp.parse_device("cpu")`; construct only safe config/resource objects. | None for this narrow check. |
| Does CUDA resolve? | `wp.get_device("cuda:0")` and `parse_device("cuda:0")` may show a visible device. | A matching NVIDIA driver/toolkit, compiled kernels, allocations, and the actual workload. |
| Does a simulator workflow run? | The adapter's import can be inspected if its dependency is installed. | The simulator package, assets, extensions, rendering/runtime, and its own device contract. |
| Is training performant/correct on GPU? | No CPU probe can establish this. | Bounded end-to-end training on the selected GPU and environment. |

Warp itself reports CUDA toolkit/driver information during initialization. Treat
any mismatch, missing compiler support, illegal memory access, or out-of-memory
failure as a CUDA runtime issue rather than silently falling back to CPU.

## Common single-agent assembly

After the environment branch has returned a Warp wrapper, the public assembly
shape is:

```python
from skrl.agents.warp.ppo import PPO, PPO_CFG
from skrl.memories.warp import RandomMemory
from skrl.trainers.warp import SequentialTrainer

# env is an already-created skrl Warp wrapper
memory = RandomMemory(memory_size=cfg.rollouts, num_envs=env.num_envs, device=env.device)
models = {"policy": policy, "value": value}
agent = PPO(
    models=models,
    memory=memory,
    cfg=cfg,
    observation_space=env.observation_space,
    state_space=env.state_space,
    action_space=env.action_space,
    device=env.device,
)
trainer = SequentialTrainer(
    cfg={"timesteps": 100_000, "headless": True},
    env=env,
    agents=agent,
)
trainer.train()
```

`SequentialTrainer` accepts a `SequentialTrainerCfg` or a dictionary and
initializes the agent with the trainer configuration. Its basic single-agent
loop handles reset, action, environment step, transition recording, and
post-interaction callbacks. Keep `timesteps` bounded while validating a new
integration. The Warp sequential implementation does not provide a completed
simultaneous-agent training path; multi-agent execution and Runner concerns
belong outside this branch.

The wrapper API is `wrap_env(env, wrapper="auto", verbose=True)`. For a
Gymnasium object, `wrapper="gymnasium"` is explicit; `"auto"` detects the
supported environment family. Do not infer that a third-party simulator is
installed merely because the wrapper name exists. Follow the environment
branch for prerequisite checks.

## Public signatures that drive construction

The installed API inspection verified these signatures (keyword arguments are
shown in abbreviated form):

| Component | Required construction inputs and useful options |
| --- | --- |
| `PPO` | `models`, optional `memory`, spaces, `device`, `cfg` |
| `DDPG` | `models`, optional `memory`, spaces, `device`, `cfg` |
| `SAC` | `models`, optional `memory`, spaces, `device`, `cfg` |
| `PPO_CFG` | `rollouts`, `learning_epochs`, `mini_batches`, `discount_factor`, `gae_lambda`, `learning_rate`, preprocessors, `ratio_clip`, `value_clip`, entropy/value scales, `kl_threshold`, `time_limit_bootstrap`, `experiment` |
| `DDPG_CFG` | `gradient_steps`, `batch_size`, `discount_factor`, `polyak`, `learning_rate`, preprocessors, `random_timesteps`, `learning_starts`, `exploration_noise`, `exploration_scheduler`, `experiment` |
| `SAC_CFG` | `gradient_steps`, `batch_size`, `discount_factor`, `polyak`, `learning_rate`, preprocessors, `random_timesteps`, `learning_starts`, `learn_entropy`, `initial_entropy_value`, `target_entropy`, `experiment` |
| `RandomMemory` | `memory_size`, `num_envs`, `device`, optional export controls and `replacement` |
| `SequentialTrainer` | `env`, `agents`, optional `scopes`, `cfg` |
| `Model` | optional observation/state/action spaces and `device`; subclass must implement `compute` |
| `DeterministicMixin` | `clip_actions`, optional role |
| `GaussianMixin` | action/mean clipping, log-std clipping bounds, `reduction` (`mean`, `sum`, `prod`, `none`), optional role |
| `wrap_env` | `env`, wrapper tag, verbosity |

Use `inspect.signature` against the installed package when resolving a version
specific detail. Do not copy a signature from a different skrl release into a
2.1.0 workflow.

## Data and persistence controls

Agent `cfg.experiment` controls `directory`, `experiment_name`,
`write_interval`, `checkpoint_interval`, `store_separately`, and optional
Weights & Biases settings. `write_interval <= 0` and
`checkpoint_interval <= 0` disable the corresponding output. The default
`"auto"` values derive intervals from trainer timesteps. Keep both intervals
at zero for a construction smoke to avoid runs and checkpoints.

Agent checkpoints are preferred over saving one model because they can include
preprocessors and other agent modules. Loading requires an equivalent model
architecture and maps to the device selected by the constructor. Warp memory
can export to `pt`, `npz`, or `csv`; export is disabled by default. Persistence
is intentionally excluded from [`warp_cpu_probe.py`](../scripts/warp_cpu_probe.py).
