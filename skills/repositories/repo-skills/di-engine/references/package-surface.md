# Package surface

This note gives future agents a compact map of the DI-engine package surface.
Use it when you need to decide which sub-skill owns a request.

## Core modules

| Module | What it owns |
| --- | --- |
| `ding.config` | config loading, saving, compilation, and config templates |
| `ding.entry` | serial, parallel, distributed, eval, and data-collection launchers |
| `ding.framework` | task-based runtime, middleware, `Parallel`, and `Supervisor` |
| `ding.envs` | env wrappers, env managers, and environment supervision |
| `ding.policy` | policy implementations and policy factories |
| `ding.model` | model templates used by policies and examples |
| `ding.worker` | learners, collectors, evaluators, commanders, buffers |
| `ding.data` | replay buffers, loaders, and storage helpers |
| `ding.rl_utils` | RL math helpers such as returns, exploration, and rescaling |
| `ding.torch_utils` | tensor, checkpoint, network, and device helpers |
| `ding.utils` | general helpers, registries, logging, file, and system utilities |
| `ding.reward_model` | reward-model and imitation-learning helpers |
| `ding.world_model` | world-model components for model-based workflows |
| `ding.example` | framework-based example recipes |
| `dizoo` | environment-specific configs, env adapters, and demos |

## Entry points

- `ding` — main CLI for `serial`, `parallel`, `dist`, `eval`, and registry queries.
- `ditask` — multi-process/task router for framework-based workflows.

## Public workflow shape

1. Choose a config or example from `dizoo/` or `ding/example/`.
2. Compile or load the config with `ding.config`.
3. Route through `ding.entry` or `ding.framework` depending on whether the
   workflow is legacy pipeline-based or task/middleware-based.
4. Use `ding.envs` to wrap the environment and validate shapes.
5. Use `ding.policy`, `ding.model`, `ding.worker`, and `ding.data` to build the
   actual training or evaluation loop.

## Signal map

- `serial_pipeline`, `eval`, or `collect_demo_data` usually means `serial-pipelines`.
- `task.start`, `Parallel.runner`, or middleware names usually means
  `framework-runtime`.
- `DingEnvWrapper`, `BaseEnvManager`, or env shape errors usually means
  `env-integration`.
- `ding`, `ditask`, `compile_config`, or config-file parsing usually means
  `cli-config`.
