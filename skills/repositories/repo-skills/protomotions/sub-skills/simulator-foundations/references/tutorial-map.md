# Progressive tutorial map

ProtoMotions includes an eight-step tutorial sequence in the source distribution. Use the sequence as a conceptual map even when you cannot run the source scripts directly.

| Stage | Concept | What to learn |
| --- | --- | --- |
| 0 | Create simulator | Backend import order, robot config, terrain, simulator class instantiation, basic stepping with random actions. |
| 1 | Add terrain | `ComplexTerrainConfig`, terrain proportions, valid spawn locations, height queries. |
| 2 | Load robot | `robot_config()` factory, robot DOFs/actions/body names, state access. |
| 3 | Scene creation | `MeshSceneObject`, `BoxSceneObject`, object physics options, scene composition. |
| 4 | Basic environment | `BaseEnv`, `EnvConfig`, reset/step/get_obs interface, automatic resets. |
| 5 | Motion manager | `MotionLibConfig`, motion sampling, reference state queries, interpolation. |
| 6 | Mimic environment | motion tracking controls, reference state, mimic observations/rewards/terminations. |
| 7 | DeepMimic | training-oriented environment and agent wiring. |

## How to use this map in tasks

- If a user wants to learn the internals, route them through the lowest stage that introduces the missing concept.
- If a user wants to add a feature, identify which tutorial stage owns the corresponding abstraction.
- If a user reports a backend runtime error, fall back to config construction and import-order checks before running tutorial code.
- If a user asks for a custom environment, start from `BaseEnv` plus MDP components rather than editing a monolithic environment class.

## Backend cautions

The tutorial scripts instantiate simulator backends and may require GPU or viewer support. A CPU-only environment can often parse configs and import helpers, but it cannot prove full tutorial runtime for IsaacGym, IsaacLab, Newton, or Genesis.
