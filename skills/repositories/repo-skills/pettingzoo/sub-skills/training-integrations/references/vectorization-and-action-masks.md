# Vectorization and Action Masks

Training integrations usually fail at boundaries between PettingZoo's multi-agent APIs and framework-specific single-agent, vector, or masked-action assumptions. Decide the API shape first, then preserve masks and live-agent semantics through each adapter.

## AEC vs Parallel Selection

Use AEC when:

- Agents act sequentially and the framework wrapper explicitly supports PettingZoo AEC envs, such as Tianshou `PettingZooEnv` or RLlib `PettingZooEnv`.
- The environment is turn-based, action masks are exposed per current agent, or evaluation compares a trained policy against a random opponent.
- A custom single-agent adapter is needed for SB3 action masking.

Use Parallel when:

- Agents act simultaneously and the framework expects batched observations/actions.
- SuperSuit vectorization will turn a PettingZoo Parallel env into a Gymnasium/SB3-style vector env.
- CleanRL or RLlib recipes batch all agents from dictionaries into tensors.

Conversion cautions:

- `aec_to_parallel(aec_env)` is valid only for environments that update at cycle boundaries and are marked parallelizable.
- `parallel_to_aec(par_env)` is useful for evaluation or sequential wrappers, but it does not make a simultaneous game turn-based in a semantic sense.
- Keep reset and step signatures current: Parallel `reset` returns `(observations, infos)` and `step` returns `(observations, rewards, terminations, truncations, infos)`.
- Do not collapse `terminations` and `truncations` until a downstream framework forces a combined done value.

## Action Mask Sources

PettingZoo environments may expose legal-action masks in different places:

- Classic AEC observations often look like `{"observation": ..., "action_mask": ...}`.
- Some integrations pass masks in `info["action_mask"]`.
- Continuous-action environments usually do not use discrete action masks.
- A mask length must equal the current agent's discrete action-space size.

When adapting a recipe:

1. Locate the mask at the boundary nearest the env, before framework wrappers flatten or strip observations.
2. Confirm mask dtype and shape are acceptable to the framework.
3. Preserve the raw observation separately from the mask when a model should not consume the mask as state.
4. Use masked random sampling for opponents or smoke tests: `env.action_space(agent).sample(action_mask)` when the space supports it.
5. Decide how to handle all-zero masks; usually treat as an environment bug or terminal-state handling bug rather than silently sampling.

## Framework Mask Patterns

### Tianshou

- Wrap AEC envs with Tianshou `PettingZooEnv`.
- Build a `MultiAgentPolicyManager` containing the trainable policy and opponent policies.
- If the observation space is a dict, derive neural-network shape from the `observation` subspace while letting the wrapper/policy path see the mask.
- Re-check mask behavior when changing Tianshou versions; tutorial requirements pin an older Tianshou release.

### Stable-Baselines3 MaskablePPO

- SB3 does not natively train PettingZoo multi-agent envs.
- For Connect Four-style AEC masking, adapt the env to a Gymnasium-like current-agent view.
- Strip `action_mask` out of the observation returned to the policy.
- Provide a separate `mask_fn(env)` to `ActionMasker` so `MaskablePPO` can query the current legal actions.
- The wrapper assumes homogeneous agent spaces; rewrite it for heterogeneous spaces.

### RLlib

- For AEC card games, preserve dict observations containing `observation` and `action_mask`.
- A custom Torch model can add a log-mask to action logits: legal actions remain unchanged and illegal actions receive a large negative value.
- Multi-agent policy mapping should match PettingZoo agent ids or a deliberate parameter-sharing scheme.

### AgileRL

- Connect Four DQN curriculum and self-play recipes pass `action_mask` into action selection for both trainable agents and opponents.
- Vectorized continuous-action recipes may use `info["agent_mask"]` rather than discrete action masks; distinguish agent availability masks from legal-action masks.

### LangChain

- Prompt the LLM with legal action indices from the mask.
- Parse and validate the response before calling `env.step`.
- Fall back to masked random sampling after bounded retries.
- Do not call hosted LLMs without user-approved credentials and network access.

## SuperSuit and Vector Wrappers

Common SuperSuit steps in PettingZoo tutorials:

- Image preprocessing: color reduction, dtype conversion, resize, normalize, and frame stack.
- PettingZoo to vector: `pettingzoo_env_to_vec_env_v1(env)`.
- Vector concatenation: `concat_vec_envs_v1(env, n, num_cpus=..., base_class="stable_baselines3" or "gymnasium")`.

Checklist before vectorizing:

1. Start from a Parallel env when possible.
2. Ensure all agents have compatible observation and action spaces.
3. For environments with changing live-agent sets, use a framework-supported death/black-death strategy or choose a different integration.
4. Match `base_class` to the downstream consumer.
5. Keep vector counts and CPU counts low for smoke tests.
6. Avoid `human` rendering in vector envs; use `rgb_array` only when image arrays are explicitly needed.

## Evaluation Loops

Training and evaluation may use different API views.

- SB3 vector tutorials train through Parallel/SuperSuit vector envs but evaluate through AEC `env()` loops to compare a shared trained model against random agents.
- SB3 action-mask tutorials train and evaluate through an AEC-derived current-agent adapter, then run an AEC loop for win-rate reporting.
- CleanRL Parallel recipes often evaluate in a fresh non-vectorized env and convert between dict observations and tensors.
- RLlib render scripts load checkpoints and use framework policy APIs; these require trained artifacts and should be opt-in.
- LangChain examples are evaluation/interaction loops, not learning loops.

Safe evaluation defaults:

- Use `render_mode=None` unless the user asks for display or video.
- Limit games, cycles, and timesteps.
- Seed envs and spaces when comparing behaviors.
- Close envs after use, but be aware some vector wrappers have close-time issues; record rather than mask such failures.

## Adapting Pistonball to SB3/SuperSuit

For a Pistonball Parallel recipe:

1. Install or confirm the Butterfly extra separately from SB3/SuperSuit packages.
2. Construct `pistonball_v6.parallel_env(...)` with bounded `max_cycles` for smoke tests.
3. Apply visual preprocessing wrappers appropriate for image observations.
4. Convert with `pettingzoo_env_to_vec_env_v1` and concatenate with `base_class="stable_baselines3"`.
5. Use one shared SB3 policy for all agents unless implementing a custom multi-policy strategy outside the tutorial scope.
6. Treat the tutorial's Pistonball SB3 path as fragile because it is documented as SuperSuit-broken; prefer validation by imports and shape inspection before training.

Dependency split:

- PettingZoo extra: `pettingzoo[butterfly]` for Pistonball and its rendering/physics dependencies.
- Vector wrapper: `supersuit`.
- Framework: `stable-baselines3` and optionally `sb3-contrib` for maskable algorithms.
- Compute/render extras: PyTorch backend, display/video libraries, and any user-requested logging tools.
