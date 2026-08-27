# External integrations and loaders

These routes are public API boundaries, not portable smoke tests. Inspect the simulator's own installation and task-registration instructions first, then use the matching skrl framework extra and wrapper. Do not install an external simulator, download assets, launch a renderer, or claim a result from this reference.

## Isaac Lab

The framework loaders are:

```python
from skrl.envs.loaders.torch import load_isaaclab_env
from skrl.envs.wrappers.torch import wrap_env

env = load_isaaclab_env(task_name="<registered-task>", num_envs=<N>, headless=True)
env = wrap_env(env, wrapper="isaaclab")
```

Use the analogous `jax` or `warp` imports for those framework routes. The loader accepts `task_name`, `num_envs`, `headless`, `cli_args`, `show_cfg`, and an optional `argparse.ArgumentParser`. It integrates Isaac Lab's CLI: `--task`, `--num_envs`, `--seed`, `--disable_fabric`, `--distributed`, plus launcher arguments. Command-line values take priority over function arguments. A task name is mandatory, and a missing name raises `ValueError` before simulator launch.

`load_isaaclab_env` imports the simulator application and task package, parses the task configuration, constructs the environment, and registers cleanup of the simulator app. Its process must be started through the simulator's supported launcher when required (the docs show an `isaaclab -p ... --task ...` style invocation). Use `headless=True` or the simulator's CLI flag for non-rendering execution; a trainer-level headless setting cannot override a loader/launcher CLI decision. Expect failures when the simulator package, registered task, assets, launcher, graphics/runtime libraries, or compatible GPU are missing. Keep those failures separate from a skrl wrapper bug.

Single-agent and multi-agent Isaac Lab wrappers are both exposed in Torch and JAX, with the Warp module also defining the corresponding wrapper classes. Choose explicitly when the environment is ambiguous:

- `"isaaclab-single-agent"` returns the single-agent `Wrapper` route;
- `"isaaclab-multi-agent"` returns the multi-agent route;
- `"isaaclab"` uses `possible_agents` on `env.unwrapped` to select multi-agent, otherwise single-agent.

The multi-agent route returns per-agent dictionaries and belongs with [multi-agent-and-runner](../../multi-agent-and-runner/SKILL.md). Isaac Lab uses PyTorch-backed simulation in common deployments; a JAX experiment may therefore share GPU pressure with PyTorch. The installation guidance recommends reducing JAX GPU preallocation (for example with `XLA_PYTHON_CLIENT_MEM_FRACTION`) when an actual Isaac/JAX run reports allocation or illegal-memory-access errors. This is a deployment workaround, not a CPU verification result.

## ManiSkill

ManiSkill environments are registered by importing ManiSkill before `gym.make`:

```python
import gymnasium as gym
import mani_skill.envs
from skrl.envs.wrappers.torch import wrap_env

env = gym.make(
    "<registered-task>",
    num_envs=<N>,
    obs_mode="state",
    sim_backend="<backend>",
    control_mode="<mode>",
)
env = wrap_env(env, wrapper="mani-skill")
```

Use the JAX or Warp wrapper import when that is the consumer framework. The public examples use a vectorized task and simulator-specific settings such as `physx_cuda`; do not copy those settings into a CPU smoke. The optional package, simulator backend, assets, and device support must match the ManiSkill release. Registration errors, unknown task ids, unsupported observation/control modes, or backend/driver failures occur before skrl conversion and should be diagnosed in ManiSkill first.

## MuJoCo Playground

Loaders are exposed under `skrl.envs.loaders.torch`, `.jax`, and `.warp`; the underlying environment is JAX-oriented. A typical route is:

```python
from skrl.envs.loaders.jax import load_playground_env
from skrl.envs.wrappers.jax import wrap_env

env = load_playground_env(
    task_name="<registered-task>",
    num_envs=<N>,
    episode_length=<length>,
    action_repeat=<repeat>,
    full_reset=False,
    randomization=False,
)
env = wrap_env(env, wrapper="playground")
```

The loader accepts task name, number of environments, episode length, action repeat, full reset, randomization, config overrides, show-config, and an optional parser. CLI values take priority over function values. Missing task, environment count, required episode length, or an invalid task can raise `ValueError`. The docs show a public registry probe (`mujoco_playground.registry.ALL_ENVS`) to list available tasks. The task package, MuJoCo runtime, JAX version, assets, and a compatible accelerator/runtime are external prerequisites.

Torch and Warp wrapper routes are present for Playground integration, but the loader's implementation is JAX based. Choose the framework based on the downstream array/model stack and confirm its optional dependencies before constructing agents.

## Related boundaries

- Shimmy compatibility adapters belong to the standard wrapper route described in [standard-environments.md](standard-environments.md); Shimmy itself does not add a tag.
- PettingZoo is a multi-agent boundary, including Shimmy's multi-agent compatibility environments. It is supported by Torch and JAX PettingZoo wrappers; route it to [multi-agent-and-runner](../../multi-agent-and-runner/SKILL.md).
- The Warp module's source does not define general Gym or PettingZoo wrapper implementations in this release. Use a supported Warp tag only after checking the concrete class/module, and prefer Gymnasium for a bounded Warp smoke.
- Real-world/robot examples, credentials, ROS middleware, and physical hardware are excluded. Do not infer support for them from the external simulator wrappers.
