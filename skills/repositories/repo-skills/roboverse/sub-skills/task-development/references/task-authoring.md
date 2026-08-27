# Task Authoring and Validation

## Ownership check

Create the change in RoboVerse when it adds or modifies a task, robot, scene,
reward, observation, demo/replay behavior, or learning entry point. Change
MetaSim first when the missing piece is a scenario-config type, registry
behavior, simulator handler/backend, or core environment abstraction.

## Minimal task pattern

RoboVerse tasks use MetaSim's declarative configuration and registry:

```python
from metasim.constants import PhysicStateType
from metasim.scenario.scenario import ScenarioCfg, SimParamCfg
from metasim.task.registry import register_task
from metasim.task.rl_task import RLTaskEnv
from metasim.utils import configclass

@register_task("family.task_name", "task_name_rl")
class ExampleTask(RLTaskEnv):
    scenario = ScenarioCfg(...)

    def _observation(self):
        ...

    def _reward(self):
        ...
```

Use the installed MetaSim signatures as authoritative: hook names may differ by
task base class/version. Follow a nearby task family for lifecycle ordering, but
keep the new task additive and do not edit unrelated legacy files to make it
work.

## Authoring sequence

1. **Select a family.** Extend an existing family when the task is a variant.
   Choose a canonical registry name and any stable alias deliberately.
2. **Compose the scenario.** Define robots, objects, cameras, ground, initial
   states, and simulation parameters using existing config objects.
3. **List state dependencies.** For each observation/reward/success term, name
   the robot/object/body/joint/site/contact field it reads.
4. **Register extras.** If a required value is not in standard RoboVerse state,
   declare it in the task's extra specification using the installed MetaSim
   query types (for example site position/matrix or contact data), or add a
   narrowly scoped query. Do not read undocumented simulator internals.
5. **Implement lifecycle hooks.** Reset all per-environment buffers, derive
   batch shapes from environment count, preserve device/dtype, and seed every
   random branch through the environment's reset contract.
6. **Define reward and termination independently.** Success, termination, and
   truncation must have documented shapes and semantics. Reward terms should be
   inspectable individually during parity work.
7. **Register/import.** Confirm package discovery imports the module and that
   both the canonical task id and intended alias resolve.
8. **Validate.** Run construction/import, reset, one bounded step, observation
   shape, reward shape/dtype, terminated/truncated shape, deterministic reset,
   and invalid-config tests before a long rollout.

## Parity-safe porting

When porting from ManiSkill, MJLab, robosuite, or another source, first make the
task run end-to-end. Then compare observations/rewards on aligned state. Avoid
claiming parity when both implementations are broken or when only a rendered
trajectory looks similar. For a reward discrepancy, record each term, tensor
shape, dtype, scale, clipping, joint/body order, quaternion convention, and
termination timing.

A trained policy's closed-loop transfer is a separate claim from observation or
reward agreement. State the backend used to train and the backend actually
executed.

## Focused test matrix

- config validation: required robot/scene/asset fields and invalid names;
- registration: canonical name and aliases resolve after package import;
- reset: same seed produces expected deterministic state; all buffers reset;
- observation/reward: exact batch shape, dtype, and finite values;
- termination: vector shape and independent termination/truncation semantics;
- ordering: explicit joint, finger, body, and camera ordering;
- extras: every requested site/contact/sensor exists on selected backends;
- parity: measured maximum/mean absolute delta and named backends.

Use simulator-backed tests only for affected backends. Report missing GPU or
system runtimes as environment blockers rather than ordinary test failures.
