# MARL Overview

## Purpose

Read this when a user asks how AI-Optimizer frames multi-agent reinforcement learning, which easy-MARL algorithm family to use, or how a request maps to the tutorial code. This reference distills the AI-Optimizer MARL overview and the easy-MARL implementation evidence into a self-contained operating map.

## Scope boundary

AI-Optimizer documents a broad MARL taxonomy: scalability/curse of dimensionality, non-stationarity, credit assignment, exploration-exploitation, hybrid action, and partial observability. The repository overview also mentions research works such as API, ASN, QPD, PMIC, and hybrid-action methods. In this generated skill, use those items as conceptual context only. The practical runtime surface covered here is the easy-MARL tutorial implementation.

The `multiagent-rl/core` area is empty in the inspected tree, and external SMAC/API-network material is not bundled here. Do not claim those workflows are executable from this sub-skill.

## MARL challenge map

| Challenge | Operational meaning | easy-MARL relevance |
| --- | --- | --- |
| Scalability / curse of dimensionality | Joint state-action spaces grow quickly with agent count. | VDN and QMIX illustrate value decomposition/mixing on cooperative tasks; CommNet illustrates communication-style Q networks at source level. |
| Non-stationarity | Each learner sees other changing policies during training. | Independent methods such as IDQN, IDDPG, and IPPO are useful baselines but are exposed to this issue. |
| Credit assignment | Team reward must be related back to individual agents. | VDN sums individual Q-values; QMIX mixes individual Q-values with state-conditioned non-negative weights; DQN/DDPG/PPO loops record team reward and per-agent signals where available. |
| Exploration-exploitation | Multi-agent exploration can disturb coordination. | DQN workflows use epsilon-greedy exploration and linear epsilon decay; DDPG has an exploration helper in source but the main loop leaves it as a TODO. |
| Hybrid action | Some domains combine discrete choices with continuous parameters. | Not implemented by easy-MARL; route elsewhere or treat as unsupported. |
| Partial observability | Agents act from local observations rather than full state. | easy-MARL agents receive per-agent observation lists; centralized information is used by some mixers/critics through state or concatenated observations/actions. |

## easy-MARL algorithm families

| Family | Agents | Entry script | Environment types | Notes |
| --- | --- | --- | --- | --- |
| DQN-based | `IDQN`, `VDN`, `QMIX`, source-level `CommNet` | `main_dqn.py` | Discrete only: `discrete_meeting`, `discrete_magym` | `IDQN` trains per-agent DQN losses; `VDN` sums per-agent Q-values; `QMIX` uses a state-conditioned monotonic mixer; `CommNet` has a communication-style Q network but needs dispatch/buffer repair before it should be trusted for training. |
| DDPG-based | `IDDPG`, `MADDPG` | `main_ddpg.py` | Continuous only: `continuous_meeting`, `continuous_mpe` | Actor networks output continuous actions with `tanh`; `MADDPG` critics consume concatenated all-agent observations/actions. The main loop does not currently apply its exploration-noise helper. |
| PPO-based | `IPPO`, `MAPPO` | `main_ppo.py` | Discrete or continuous easy-MARL environments | The PPO entry handles both discrete and continuous environment metadata and trains once per episode from an episode buffer. `MAPPO` adds centralized state/critic information compared with `IPPO`. |

## Environment families

| Environment | Action type | Scenario argument | Operational notes |
| --- | --- | --- | --- |
| `discrete_meeting` | Discrete movement in a small 2D meeting task | Not used | Two agents try to meet a target. The environment exposes local observations, a concatenated state, and five discrete movement actions. Rendering is not implemented. |
| `continuous_meeting` | Continuous 2D movement | Not used | Two agents move in a bounded plane with `Box(-1, 1, shape=(2,))` actions. Rendering is not implemented. |
| `discrete_magym` | Discrete MAGYM-style registered tasks | Required | The wrapper registers tasks including Switch, Combat, PongDuel, PredatorPrey, TrafficJunction, Checkers, and Lumberjacks variants. Use explicit scenarios such as `Switch4-v0` or `Combat-v0`. |
| `continuous_mpe` | Continuous MPE particle tasks | Required | The wrapper loads vendored scenario modules by name, such as `simple_tag`, `simple_spread`, `simple`, `simple_adversary`, `simple_crypto`, `simple_push`, `simple_reference`, `simple_speaker_listener`, and `simple_world_comm`. |

## Practical route decisions

- If the user wants a beginner MARL tutorial command, start with `discrete_meeting` + `IDQN`, `VDN`, `QMIX`, `IPPO`, or `MAPPO`, or `continuous_meeting` + `IDDPG`, `MADDPG`, `IPPO`, or `MAPPO`.
- If the user requests a named MAGYM or MPE scenario, require `--scenario-name` and verify the algorithm family supports the environment's action type.
- If the user asks for CommNet, explain that the source contains a `CommNet` class and a `main_dqn.py` branch, but the inspected hyperparameter dispatcher lacks CommNet modules and the CommNet training method does not match the current buffer dictionary interface. Treat it as an extension/repair task, not a ready training claim.
- If the user asks for API-QMIX/API-VDN/API-MAPPO/API-MADDPG, SMAC benchmark reproduction, or State-of-the-Art claims, keep the answer conceptual unless another sub-skill/root reference provides verified executable code. This sub-skill does not verify those external benchmarks.
