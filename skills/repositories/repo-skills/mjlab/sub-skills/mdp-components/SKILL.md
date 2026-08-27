---
name: mdp-components
description: "Use mjlab built-in actions, actuators, observations, rewards,
  terminations, events, commands, curricula, metrics, and task-specific MDP
  terms."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# mdp-components

Use this sub-skill when a task asks which mjlab MDP term, action config,
actuator config, command generator, reward, termination, curriculum, or
built-in task-family component to use.

## Start here

- Read [actions-actuators.md](references/actions-actuators.md) for policy action
  terms, actuator configs, scaling/offset/clip, delay, and differential IK.
- Read [mdp-term-catalog.md](references/mdp-term-catalog.md) for built-in
  observation, reward, termination, event, command, curriculum, and metric
  functions.
- Read [task-specific-mdp.md](references/task-specific-mdp.md) for velocity,
  tracking, manipulation, and cartpole term patterns.
- Read [troubleshooting.md](references/troubleshooting.md) when actions have the
  wrong dimension, rewards have the wrong sign, commands are missing, or target
  regexes fail.
- Run [scripts/inspect_mdp_terms.py](scripts/inspect_mdp_terms.py) to list
  public callables/signatures from installed mjlab MDP modules.

## Quick choices

| Need | Typical mjlab surface |
|---|---|
| Drive joints from policy output | `JointPositionActionCfg`, `JointVelocityActionCfg`, `JointEffortActionCfg`, or `RelativeJointPositionActionCfg` |
| Reuse XML actuators | `XmlActuatorCfg` on `EntityArticulationInfoCfg` |
| Stable implicit PD in MuJoCo | `BuiltinPositionActuatorCfg`, `BuiltinPdActuatorCfg`, or `BuiltinDcMotorActuatorCfg` |
| Explicit torque/PD/DC dynamics | `IdealPdActuatorCfg`, `DcMotorActuatorCfg`, `LearnedMlpActuatorCfg` |
| Robot target lookup | `SceneEntityCfg` with joint/body/geom/site/actuator names |
| Standard observations | `mjlab.envs.mdp.observations` functions |
| Standard penalties/rewards | `mjlab.envs.mdp.rewards` plus task-family rewards |
| Episode stop logic | `mjlab.envs.mdp.terminations` and task-family terminations |
| Reset or perturb states | `EventTermCfg` with event functions |

## Boundary routing

- Manager dictionary shape and lifecycle: [environment-configuration](../environment-configuration/SKILL.md).
- Entity/spec attachment and scene assembly: [scene-simulation-assets](../scene-simulation-assets/SKILL.md).
- Sensor, terrain, and domain-randomization details:
  [perception-terrain-randomization](../perception-terrain-randomization/SKILL.md).
- Task registry and CLI training/play execution:
  [training-evaluation-cli](../training-evaluation-cli/SKILL.md).
