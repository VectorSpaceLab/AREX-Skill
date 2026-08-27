---
name: environment-configuration
description: "Design and debug mjlab ManagerBasedRlEnvCfg and manager-layer configuration."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# mjlab environment configuration

Use this sub-skill when a task is about authoring or debugging mjlab's
`ManagerBasedRlEnvCfg` and manager layer: observation, action, reward,
termination, event, command, curriculum, metrics, and recorder dictionaries;
term config patterns; reset/step lifecycle; observation history, delay, noise,
and NaN policy; `SceneEntityCfg` matching; custom manager terms; auto-reset and
finite-horizon behavior.

## Read these bundled files

- [Configuration patterns](references/configuration-patterns.md) for the
  `ManagerBasedRlEnvCfg` shape, manager dictionaries, term cfg types, custom
  term signatures, observation temporal features, and `SceneEntityCfg` matching.
- [Lifecycle and managers](references/lifecycle-and-managers.md) for
  construction order, reset and step timing, manager responsibilities, horizon
  semantics, and recorder hook timing.
- [Troubleshooting](references/troubleshooting.md) for missing term names,
  tensor shape mismatches, NaN handling, command signatures, regex matching,
  event-mode requirements, and auto-reset/manual-reset problems.
- [inspect_env_config.py](scripts/inspect_env_config.py) for a safe installed
  package helper that loads a registered task and prints manager keys plus a
  compact config summary.

## Route neighboring concerns

- Physical scene composition, entities, MuJoCo simulation options, assets, and
  export internals belong to `scene-simulation-assets`.
- Choosing concrete built-in MDP functions, action configs, action dimensions,
  actuators, and task-specific MDP terms belongs to `mdp-components`.
- Sensors, terrain generation, raycasts/cameras/contacts, and domain
  randomization function catalogs belong to `perception-terrain-randomization`.
- Installed CLIs, task registry operations, training/play/export commands, and
  Tyro override syntax belong to `training-evaluation-cli`.

## Operating checklist

1. Identify the target task/config and inspect current manager keys with the
   bundled helper before changing term names or group names.
2. Map each manager entry as `string_name -> TermCfg`, then verify the callable
   signature and output shape expected by that manager.
3. Check lifecycle timing before placing side effects: reset events and
   curricula run on reset paths; actions write inside decimation; rewards and
   terminations run before auto-reset; observations are assembled after
   commands and sensors update.
4. For custom terms, decide whether a stateless function is enough or whether a
   class term is needed to cache resolved indices, keep per-episode state, or
   expose recorder/command lifecycle hooks.
5. Use the troubleshooting reference for the exact failure class before routing
   to a sibling sub-skill.
