# AI-Optimizer Repository Map

## When to read

Read this when a request names AI-Optimizer but not a specific algorithm family, when a target checkout appears incomplete, or when you need to decide which sub-skill owns a folder, command, or dependency problem.

## High-level shape

AI-Optimizer is a collection of reinforcement-learning research code and documentation. It is not one Python package with a single install command. Use the folder names below as identifiers for a target AI-Optimizer checkout.

| Area | Status in inspected snapshot | Route |
|---|---|---|
| `modelbased-rl` | Checked in; contains Dreamer, ED2-Dreamer, MBPO/ED2-MBPO, BMPO, MuZero, PlaNet, Sampled MuZero, CaDM material. | `sub-skills/model-based-rl/SKILL.md` |
| `multiagent-rl/easy-marl` | Checked in; contains tutorial MARL algorithms, environments, hyperparameters, and entry scripts. | `sub-skills/multi-agent-rl/SKILL.md` |
| `offline-rl-algorithms` | Checked in; contains offline RL train scripts, E2O/PEX, and d3rlpy-derived source. | `sub-skills/offline-rl/SKILL.md` |
| `multiagent-rl/core` | Submodule placeholder was empty/not initialized. | Mention as unavailable unless a target checkout initializes it; then refresh skill. |
| `self-supervised-rl` | Submodule placeholder was empty/not initialized. | Not covered beyond top-level README context. |
| `transfer-and-multi-task-reinforcement-learning` | Submodule placeholder was empty/not initialized. | Not covered beyond top-level README context. |
| `cornerstone` | Submodule placeholder was empty/not initialized. | Not covered. |
| `images`, `README.assets`, algorithm image folders | Concept figures and README assets. | Reference-only; not needed for command/API operation. |

## Common task routes

- "Which model-based baseline should I use for planning from pixels?" -> model-based overview, then Dreamer/PlaNet references.
- "Build a MuZero CartPole command that stays on CPU" -> model-based MuZero helper.
- "Run MAPPO on continuous MPE simple_tag" -> multi-agent easy-MARL helper.
- "Why does QMIX with continuous_mpe fail?" -> multi-agent compatibility matrix.
- "Validate my D4RL-like `.npz` before CQL" -> offline RL dataset validator.
- "Build PEX offline then online commands" -> offline RL PEX helper.
- "Use self-supervised RL or transfer/multi-task RL code from this checkout" -> report that those submodules were empty in the provenance snapshot and require a refreshed skill after initialization.

## Dependency boundaries

Do not share environments blindly across areas:

- Model-based folders mix TensorFlow 1.x/2.x, Ray, old Gym, MuJoCo, dm_control, and PyTorch.
- Easy-MARL primarily follows PyTorch/tensorboardX tutorial code and may need MAGYM/MPE dependencies for non-meeting environments.
- Offline RL depends heavily on PyTorch, D4RL, Gym/MuJoCo, d3rlpy-derived APIs, and sometimes Waymo/offline dataset utilities.

When in doubt, build commands and validate static inputs first; then prepare a task-specific runtime for the chosen algorithm family.
