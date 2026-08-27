---
name: cli-config
description: "Routes DI-engine CLI, config, and launch-parameter workflows."
metadata:
  disco-role: operating
  disable-model-invocation: true
license: Apache 2.0
disable-model-invocation: true
---

# CLI and config

Use this sub-skill for the package entry points, config compilation, and the
lightweight launch wrappers that sit in front of the training/runtime code.

## Owns

- `ding` and `ditask` command-line usage
- `ding.config` helpers: `read_config`, `read_config_directly`,
  `read_config_with_system`, `save_config`, `save_config_py`, `compile_config`,
  and `compile_config_parallel`
- config file shape: `main_config`, `create_config`, and the optional
  `system_config` used by distributed launch paths
- predefined config lookup through `ding.entry.predefined_config`
- generic launch wrappers such as `ding -m serial`, `ding -m parallel`,
  `ding -m dist`, and `ding -m eval`

## Does not own

- The detailed serial/offline/eval loops themselves; those live in
  `serial-pipelines`
- Task/middleware examples and multi-process routing internals; those live in
  `framework-runtime`
- Env-wrapper behavior and environment shape debugging; those live in
  `env-integration`

## Read this first when the user asks

- how to choose a `ding` mode or `ditask` flag
- why a config file fails to load or compile
- how `create_config` and `main_config` are supposed to pair up
- how to run the repo-provided serial or parallel wrappers from a prepared
  environment
- how to query the registry or choose a predefined CartPole/Pendulum config

## Workflow

1. Decide whether the request is about the CLI surface or the config surface.
2. Use `references/cli-reference.md` for commands, flags, and launch modes.
3. Use `references/config-reference.md` for config object structure and
   compile/save behavior.
4. Use `scripts/cli_smoke.py` when you want a bundled check for CLI help output
   plus config compilation in the installed environment.
5. If the request is really about training logic or env behavior, route to the
   neighboring sub-skill instead of growing this one.

## Common decision points

- Prefer `ding -m serial` for the legacy single-process pipeline family.
- Prefer `ding -m parallel` when the workflow is using `Parallel`-based message
  routing and multiple workers on one machine.
- Prefer `ding -m dist` only when the config contains distributed system fields
  and the user explicitly wants coordinator/collector/learner launch control.
- Prefer `ditask` when the user is working with the task router or the modern
  multi-process framework entry model.

## Helpful bundle links

- `references/cli-reference.md` for CLI flags, modes, and launch semantics.
- `references/config-reference.md` for config object shape and compile rules.
- `references/troubleshooting.md` for common parse, mode, and registry errors.
- `scripts/cli_smoke.py` for a small check that the installed package still
  parses the CLI and compiles a representative config.
