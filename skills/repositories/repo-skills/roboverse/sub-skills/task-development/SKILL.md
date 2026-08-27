---
name: task-development
description: "Guides RoboVerse task authoring, registration, observation and
  reward contracts, reset logic, callback composition, and parity-safe task
  tests."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Task Development

Use this route when adding or changing a RoboVerse task, task config, reward,
observation, reset, callback, success checker, or task registration. Decide
first whether the change belongs in RoboVerse (content and task behavior) or
MetaSim (core abstractions, registry, handlers, or simulator backend).

## Route

1. Read [task-authoring.md](references/task-authoring.md) for the smallest
   config/registration workflow and state-field checklist.
2. Compose existing MetaSim and RoboVerse config objects with `@configclass`;
   do not fork core types or work around a missing MetaSim capability in the
   downstream package.
3. Define the scenario, task class, action/observation contract, reset, reward,
   termination, and success behavior. Register the task under a stable name and
   import it through the package discovery path.
4. Add a focused regression test for every behavior fix. Run a lightweight
   reset/shape test first, then backend-specific parity checks only when the
   selected environment supports them.
5. Use [troubleshooting.md](references/troubleshooting.md) for registration,
   state/extras, shape, seed, and reward-order failures.

## Key boundaries

- Core simulator APIs, registry semantics, and backend bugs route to MetaSim.
- Task/robot/scene/reward/observation content routes here.
- External benchmark passthroughs route to
  [benchmark-integrations](../benchmark-integrations/SKILL.md).
- Measured cross-simulator comparisons route to
  [parity-and-tooling](../parity-and-tooling/SKILL.md).
