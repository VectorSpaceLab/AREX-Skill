# Framework Recipes

PettingZoo is the environment interface; training frameworks are separate optional stacks. A base PettingZoo install only requires `numpy` and `gymnasium`, while the tutorial integrations add framework packages, optional PettingZoo extras, vectorization helpers, and sometimes ROMs, display backends, GPU libraries, or credentials. Prefer isolated project environments for these recipes and do not run long training by default.

## Quick Decision Table

| Request shape | PettingZoo API | Typical environment | Integration pattern | Default validation |
| --- | --- | --- | --- | --- |
| CleanRL PPO on Pistonball | Parallel | Butterfly `pistonball_v6` | Collect per-agent batches from a Parallel env; optionally preprocess observations with SuperSuit | Inspect requirements and run import checks only |
| Tianshou Tic-Tac-Toe or Connect Four | AEC via Tianshou wrapper | Classic `tictactoe_v3` or `connect_four_v3` | Wrap `env()` with Tianshou `PettingZooEnv`; use `DummyVectorEnv`, `MultiAgentPolicyManager`, and a random opponent | Bounded wrapper/import smoke only |
| SB3 action-masked Connect Four | AEC adapted to Gymnasium | Classic `connect_four_v3` | Custom single-agent-style wrapper plus `sb3_contrib.common.wrappers.ActionMasker` and `MaskablePPO` | Unit-check wrapper shape/mask logic, no learning |
| SB3 vectorized Pistonball/KAZ | Parallel to vector | Butterfly `pistonball_v6` or `knights_archers_zombies_v10` | SuperSuit preprocess, `pettingzoo_env_to_vec_env_v1`, `concat_vec_envs_v1`, shared SB3 policy | Requirements/import check; avoid known-broken Pistonball path unless user opts in |
| Ray/RLlib Pistonball | Parallel | Butterfly `pistonball_v6` | Register env returning RLlib `ParallelPettingZooEnv`; configure PPO and optional custom CNN model | Config review/import check, no Ray cluster launch |
| Ray/RLlib Leduc Hold'em | AEC | Classic `leduc_holdem_v4` | Register env returning RLlib `PettingZooEnv`; custom masked-action model for dict observations | Verify observation/action spaces and mask model logic |
| AgileRL DQN/MADDPG/MATD3 | AEC or Parallel/vector | Classic Connect Four, Atari Space Invaders, MPE simple speaker listener | Use AgileRL multi-agent algorithms, curriculum/self-play, or `AsyncPettingZooVecEnv` | Check Python/framework compatibility only |
| LangChain PettingZoo agents | AEC | Classic RPS, Tic-Tac-Toe, poker | Wrap LLM-driven agents around PettingZoo action loops, with random fallback and action-mask prompts | Dry-run loop without LLM calls, or mock model only |

## Dependency Groups

Use these groups as starting points; exact versions may need adjustment for the user's Python and framework stack.

- CleanRL tutorial group: `pettingzoo[butterfly,atari,testing]>=1.24.0`, `SuperSuit>=3.9.0`, `tensorboard>=2.11.2`, `torch>=1.13.1`, `imageio`, `imageio-ffmpeg`.
- Tianshou tutorial group: `numpy<2.0.0`, `pettingzoo[classic]>=1.23.0`, `packaging>=21.3`, `tianshou==0.5.0`.
- SB3 Connect Four group: `pettingzoo[classic]>=1.24.0`, `stable-baselines3>=2.0.0`, `sb3-contrib>=2.0.0`.
- SB3 vector group: `pettingzoo[butterfly]>=1.24.0`, `stable-baselines3>=2.0.0`, `supersuit>=3.9.0`.
- Ray/RLlib group: `pettingzoo[classic,butterfly]>=1.24.0`, `Pillow>=9.4.0`, `ray[rllib]==2.55.0`, `SuperSuit>=3.9.0`, `torch>=1.13.1`, `tensorflow-probability>=0.19.0`.
- AgileRL group: `agilerl==2.2.1` for Python `>=3.10,<3.12`, `pettingzoo[classic,atari]>=1.23.1`, `mpe2>=1.0.0`, `AutoROM>=0.6.1`, `SuperSuit>=3.9.0`, `torch>=2.0.1`, `numpy>=1.24.2`, `tqdm>=4.65.0`, `fastrand==1.3.0`, `gymnasium>=0.28.1`, `imageio>=2.31.1`, `Pillow>=9.5.0`, `PyYAML>=5.4.1`.
- LangChain group: `pettingzoo[classic]`, `langchain`, `openai`, `tenacity`.

Run `scripts/inspect_integration_requirements.py --check-imports cleanrl tianshou sb3-vector` from this sub-skill directory, or pass `--json`, to inspect these groups without installing packages.

## CleanRL PPO

CleanRL-style recipes are useful when the user wants a transparent PyTorch training loop rather than a framework trainer.

- Environment choice: the basic recipe uses Butterfly `pistonball_v6.parallel_env(render_mode="rgb_array", continuous=False, max_cycles=...)`; the advanced recipe can import Atari Parallel environments dynamically.
- Preprocessing: use SuperSuit-style color reduction, resizing, and frame stacking before batching observations.
- API pattern: call `ParallelEnv.reset(seed=...) -> (observations, infos)`, convert observation/reward/termination/truncation dictionaries into arrays in possible-agent order, pass an action dictionary into `step`, and close the env.
- Vectorization: the advanced recipe converts the Parallel env to a Gymnasium-like vector env with SuperSuit, then concatenates vector envs for larger rollouts.
- Logging caveats: the advanced recipe includes TensorBoard and optional Weights & Biases integration; treat external tracking as credential/network work and ask before enabling it.
- Validation: inspect imports and confirm the env can be constructed with the chosen extras. Do not run PPO loops unless the user explicitly accepts compute and checkpoint writes.

Adaptation steps:

1. Confirm the target env has a Parallel API or can be safely converted.
2. Choose observation preprocessing compatible with the observation space: image wrappers for image spaces, no image CNN for vector observations.
3. Preserve dictionary-to-batch ordering using `env.possible_agents` or stable live-agent order.
4. Track both `terminations` and `truncations`; do not collapse them into old `done` terminology unless the target framework requires a combined signal.
5. Gate TensorBoard/WandB, video capture, and GPU-specific settings behind user confirmation.

## Tianshou

Tianshou recipes are useful for AEC games with a trainable policy against random or fixed opponents.

- Environment choice: the tutorial uses Classic `tictactoe_v3.env()` and wraps it with `tianshou.env.pettingzoo_env.PettingZooEnv`.
- Vectorization: provide callables to `DummyVectorEnv`, not already-created env instances.
- Policy layout: construct one `DQNPolicy` for the learner, one `RandomPolicy` for the opponent, then combine them with `MultiAgentPolicyManager`.
- Action masks: Classic env observations are often dictionaries with `observation` and `action_mask`. Ensure the network sees only the observation tensor while the policy/wrapper receives the legal-action mask according to the Tianshou version in use.
- Reward metric: select the learner column from the multi-agent reward array, as in the Tic-Tac-Toe recipe.
- Validation: import `tianshou`, wrap a single env, reset, and sample one collector step only when the user approves framework execution.

Adapting Tic-Tac-Toe to Connect Four:

1. Replace the env factory with `connect_four_v3.env()` and keep the Tianshou `PettingZooEnv` wrapper.
2. Recompute observation and action shapes after wrapping; Connect Four uses a different board observation and action count.
3. Preserve a random or scripted opponent policy during initial validation to avoid self-play complexity.
4. Confirm action masks still flow through the wrapper before training; invalid columns in Connect Four must remain masked.
5. Lower vector count, epochs, and replay sizes for smoke runs; treat full training as opt-in.

## Stable-Baselines3

SB3 is primarily single-agent. PettingZoo tutorials demonstrate adapters and shared-policy tricks rather than native multi-agent training.

### Action-Masked AEC Recipe

- Environment choice: Classic `connect_four_v3.env()`.
- Adapter: create a wrapper that subclasses PettingZoo `BaseWrapper` and Gymnasium `Env`, exposes one current-agent observation/action space, strips `action_mask` from `observe`, and exposes a separate `action_mask()` method.
- Masking: wrap with `sb3_contrib.common.wrappers.ActionMasker`; use `MaskablePPO`, not plain PPO, for invalid action masking.
- Evaluation: run an AEC loop where one side may sample from `env.action_space(agent).sample(action_mask)` and the trained side calls `model.predict(observation, action_masks=action_mask, deterministic=True)`.
- Assumptions: the tutorial wrapper assumes each agent has the same observation and action spaces. Do not reuse unchanged for heterogeneous custom envs.
- Caveat: the Connect Four docs note Gymnasium version compatibility issues for newer Gymnasium releases; validate imports before training.

### SuperSuit Vector Recipe

- Environment choice: Butterfly `pistonball_v6.parallel_env()` or `knights_archers_zombies_v10.parallel_env()`.
- Preprocessing: apply observation preprocessing such as color reduction, resize, and frame stack for visual spaces.
- Vectorization: call `ss.pettingzoo_env_to_vec_env_v1(env)`, then `ss.concat_vec_envs_v1(..., base_class="stable_baselines3")`.
- Shared policy: one SB3 policy controls all agents; this is demonstration-style parameter sharing, not a full multi-agent algorithm.
- Evaluation: train through the Parallel/vector path, then evaluate with the AEC API for easy random-agent comparisons.
- Caveat: the Pistonball SB3 tutorial declares a SuperSuit-related breakage; prefer KAZ or another confirmed vector path unless the user explicitly wants to debug it.

## Ray/RLlib

RLlib recipes are useful when the user expects distributed rollout workers, explicit multi-agent policies, or registered environments.

- Parallel Pistonball: create a PettingZoo Parallel env, apply SuperSuit image preprocessing, wrap it in `ray.rllib.env.wrappers.pettingzoo_env.ParallelPettingZooEnv`, register it with Ray, and configure PPO.
- AEC Leduc Hold'em: wrap `leduc_holdem_v4.env()` with RLlib `PettingZooEnv`, register a custom masked-action model, and configure per-agent policies.
- Action mask model: for dict observations, combine model logits with `log(action_mask)` clamped to a large negative floor so illegal actions receive near-impossible logits.
- Resource controls: `ray.init`, rollout workers, GPU counts, storage paths, and checkpoints all create nontrivial side effects; ask before launching.
- Validation: review config and import modules first. If a smoke run is allowed, lower `num_rollout_workers`, stop timesteps, checkpoint frequency, and render settings.

## AgileRL

AgileRL recipes are useful for multi-agent algorithms, curriculum learning, evolutionary hyperparameter optimization, and self-play.

- DQN curriculum/self-play: Classic Connect Four with action masks, lesson configs, random/scripted opponents, and staged opponent difficulty.
- MADDPG: Atari Space Invaders Parallel env with SuperSuit preprocessing and AgileRL vectorization.
- MATD3: MPE simple speaker listener Parallel env with continuous actions and `AsyncPettingZooVecEnv`.
- Vectorization: AgileRL recipes commonly use `AsyncPettingZooVecEnv([lambda: env for _ in range(num_envs)])`; ensure factories create independent envs when adapting beyond tutorial smoke code.
- Masks: Connect Four curriculum and render loops pass `action_mask` into policy action selection; preserve this when changing opponents or lessons.
- Version caveat: the tutorial states AgileRL supports Python `<3.12`; reconcile this with PettingZoo's broader Python support before installing.
- Validation: check Python version and imports only by default. Treat AutoROM, Atari ROMs, pretrained weights, GPU, and render scripts as opt-in.

## LangChain

LangChain recipes are agent-simulation examples, not RL training.

- Environment choice: Classic RPS, Tic-Tac-Toe, and poker examples use AEC loops with `render_mode="human"` in the tutorial; prefer `render_mode=None` or text/ansi modes for headless validation.
- Agent adapter: subclass a Gymnasium-style agent wrapper to add the PettingZoo agent name and sample actions with `env.action_space(name)`.
- Action masks: an action-mask-aware agent should read `observation["action_mask"]`, instruct the LLM to choose only legal indices, and fall back to random masked sampling after repeated invalid outputs.
- Credentials/network: OpenAI or other hosted model calls require credentials and network access; ask before running them.
- Validation: use a mock or deterministic local model response, or replace LLM selection with random masked sampling, to test PettingZoo loop mechanics without credentials.

## Safe Validation Strategy

1. Run the requirements inspector to identify required package groups and importable modules.
2. Confirm PettingZoo family extras separately from framework packages.
3. Construct the target env with small `max_cycles` and non-GUI rendering only if optional dependencies are installed.
4. Validate adapter shapes, action masks, and reset/step signatures without learning.
5. Escalate to short training only after user approval for package installs, compute, checkpoints, logs, display, network, and credentials.

## Explicit Skip Defaults

Skip native tutorial execution by default when it involves long training, Ray clusters, checkpoint/model writes, TensorBoard/WandB, GPU assumptions, GUI rendering, ROM installation, OpenAI or hosted LLM credentials, network calls, or framework installation. Provide a concrete reduced command plan instead of running it automatically.
