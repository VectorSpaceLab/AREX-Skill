# Troubleshooting Training Integrations

Use this guide to diagnose integration failures before installing frameworks or launching training. Most issues are dependency isolation, stale framework APIs, action-mask shape mismatches, vectorization assumptions, rendering, or unapproved external services.

## Missing Framework Packages

Symptoms:

- `ModuleNotFoundError: No module named 'tianshou'`, `stable_baselines3`, `sb3_contrib`, `ray`, `agilerl`, `supersuit`, `langchain`, or `openai`.
- PettingZoo imports work, but tutorial imports fail.

Fix strategy:

1. Identify the recipe group with `scripts/inspect_integration_requirements.py --groups`.
2. Separate PettingZoo extras from framework packages.
3. Ask before installing anything; framework stacks can be large and version-sensitive.
4. Prefer an isolated environment per framework family.
5. Re-run import checks before constructing envs or trainers.

Do not install `[all]` as a reflex. Use the smallest PettingZoo extra for the environment family, then add only the framework packages needed for the chosen tutorial.

## Missing PettingZoo Extras

Symptoms:

- `ModuleNotFoundError` for `pygame`, `pymunk`, `Box2D`, `multi_agent_ale_py`, `rlcard`, `shimmy`, or OpenSpiel-related modules.
- Base PettingZoo works, but Classic/Butterfly/Atari/SISL env construction fails.

Fix strategy:

- Classic board/card examples such as Tic-Tac-Toe, Connect Four, and Leduc Hold'em usually need `pettingzoo[classic]`.
- Butterfly image/physics examples such as Pistonball and KAZ usually need `pettingzoo[butterfly]`.
- Atari examples need `pettingzoo[atari]` and ROM handling; ROM acquisition is not a default safe action.
- MPE examples in AgileRL use `mpe2`, which is separate from PettingZoo base extras.

Route detailed family selection and optional dependency troubleshooting to `../environment-families/SKILL.md`.

## Incompatible API Versions

Symptoms:

- Import names moved, wrappers reject current Gymnasium APIs, or reset/step return arity differs.
- SB3 Connect Four docs note incompatibility with Gymnasium versions newer than a known range.
- Tianshou tutorial pins `tianshou==0.5.0` and older comments may mention older PettingZoo versions.
- AgileRL tutorial states Python `<3.12` support.

Fix strategy:

1. Check Python version and installed package versions before editing code.
2. Compare the framework's current wrapper API with the recipe assumptions.
3. Preserve PettingZoo's current reset/step signatures and adapt at the framework boundary.
4. Prefer small adapter tests over long training to expose version mismatches.
5. If the user needs exact tutorial reproduction, propose a fresh isolated environment matching the tutorial requirements.

## Action Mask Shape or Space Mismatch

Symptoms:

- Illegal actions are sampled despite masks.
- `MaskablePPO` complains about mask shape.
- RLlib custom model errors around dict observations or logits.
- Tianshou model shape uses a dict observation instead of the raw `observation` subspace.

Fix strategy:

- Confirm the current agent's action space is discrete and mask length equals `action_space(agent).n`.
- For dict observations, split `observation` from `action_mask` before feeding neural networks.
- For SB3, expose `action_mask()` through `ActionMasker`; do not pass mask arrays as normal observations.
- For RLlib, ensure the custom model sees both `observation` and `action_mask` keys and adds a log-mask to logits.
- For random opponents, sample with the mask when supported: `env.action_space(agent).sample(action_mask)`.
- Treat all-zero masks as a bug unless the agent is already terminated/truncated.

Route core mask-loop semantics to `../use-environments/SKILL.md`.

## AEC, Parallel, and Vectorization Mismatch

Symptoms:

- `aec_to_parallel` asserts or produces inconsistent steps.
- SuperSuit vector wrappers reject changing agent counts.
- SB3 receives dicts keyed by agent instead of vector observations.
- RLlib policy mapping does not match PettingZoo agent ids.

Fix strategy:

1. Choose AEC or Parallel deliberately for the framework.
2. Use Parallel for SuperSuit vectorization when possible.
3. Use AEC for turn-based masked games and random-opponent evaluation loops.
4. Verify homogeneous spaces before shared-policy/vector recipes.
5. For live-agent changes, use framework-supported black-death/death masking or select an env with stable agent sets.
6. Keep smoke vector counts small and disable GUI rendering.

Route conversion-wrapper details to `../wrappers-and-utilities/SKILL.md`.

## GUI, Rendering, and Video Failures

Symptoms:

- `pygame` display errors, missing `DISPLAY`, headless CI failures, video recorder errors, or RGB array shape assumptions.
- Tutorial render scripts require trained checkpoints.

Fix strategy:

- Use `render_mode=None` for validation unless the user asks for display.
- Use `render_mode="rgb_array"` only when the framework expects image observations or video arrays.
- Avoid `render_mode="human"` in headless environments.
- Do not run render scripts that load checkpoints unless the user provides or approves model artifacts.
- Disable video capture and external logging by default.

## Long Training, Checkpoints, and GPU Assumptions

Symptoms:

- Tutorials take minutes to hours, use `torch.cuda.is_available()`, start Ray workers, save `.zip`/`.pt` checkpoints, or write logs.
- CI-reduced timesteps still perform nontrivial training.

Fix strategy:

1. Ask before training, launching Ray, writing checkpoints, using GPU, or allocating long runs.
2. Offer a short validation alternative: import checks, env construction, one reset/step, adapter shape checks, or dry-run config generation.
3. If approved, lower timesteps, rollout workers, vector env count, and episodes explicitly.
4. Keep outputs in a user-approved working directory and report expected writes.
5. Do not assume GPU availability; make device selection explicit.

## Credentials and Network for LangChain or Logging

Symptoms:

- Missing `OPENAI_API_KEY`, hosted model failures, network timeouts, WandB login prompts, or external telemetry.

Fix strategy:

- Ask before network use or credential-dependent execution.
- Use mock models or deterministic local responses for PettingZoo loop validation.
- Disable WandB, hosted LLM calls, and remote logging by default.
- Bound LLM retries and fall back to masked random actions when parsing fails.

## Requirements Inspector Problems

Symptoms:

- The inspector reports modules missing even though packages are installed under different import names.
- Requirement markers skip packages for the current Python version.

Fix strategy:

- Treat inspector output as a local diagnostic, not an installer.
- Check package metadata with the user's package manager if import names differ.
- Respect environment markers, especially AgileRL's Python range.
- Run `scripts/inspect_integration_requirements.py --help` to inspect supported groups and options.
