# Baseline Families

This reference summarizes ManiSkill's baseline ecosystem and the main family-level decisions that matter for safe planning. Treat the exact training launchers as reference-only unless the user explicitly wants to run them.

## Families at a glance

| Family | Methods | Main idea | Notes |
| --- | --- | --- | --- |
| Online RL | PPO, SAC, TD-MPC2 | Learn from reward with on-policy or off-policy updates | PPO is the most general-purpose entry point; SAC has state and image variants; TD-MPC2 is model-based and sensitive to evaluation settings. |
| Imitation / supervised IL | BC, ACT, Diffusion Policy | Learn from replayed or collected demonstrations | These workflows depend on demo quality and often need longer horizons than the environment default. |
| Online learning from demonstrations / offline RL | RFCL, RLPD | Combine demonstrations with online interaction or replayed prior data | These methods are more sensitive to backend alignment and external dependencies. |
| Experimental / adjacent | SAC+Demos, SAC-MoE | Additional reference material around demo-augmented RL | Useful as context, but not part of the stable core family map. |

## Online RL details

### PPO
- A strong default when you want a broad benchmark baseline.
- Supports state-based and visual-based workflows.
- A faster path exists for performance-oriented experimentation, but it usually needs extra torch ecosystem packages.
- Exact launcher flags are training-scale and intentionally not bundled here.

### SAC
- Stable for many state-based ManiSkill tasks.
- Visual variants are more memory-sensitive than state-only runs.
- Keep observation size and image resolution conservative when you are just comparing setups.

### TD-MPC2
- Model-based continuous-control baseline.
- Evaluation is sensitive to matching `control_mode` and the evaluation environment count with the training setup.
- Treat the current docs and configs as the source of truth for supported settings.

## Imitation / supervised IL details

### BC
- Supervised imitation on demonstrations.
- Works best when demo length and observation format are standardized.
- If the demonstrations are slow, plan for a longer episode limit than the default.

### ACT
- Transformer-based action chunking on demos.
- Shares the same episode-length caution as BC.
- Good when the trajectory horizon is longer or the action chunking matters.

### Diffusion Policy
- Demo learning baseline for state and image modalities.
- Most explicit multimodal-demo baseline in the set.
- Be cautious with large image stacks until the evaluation protocol is stable.

## Online demo learning / offline RL details

### RFCL
- Sparse-reward demo efficiency with curriculum-like structure.
- Often tied to a JAX-based ecosystem or other external dependencies.
- Best treated as a reference family when the user asks about demo-efficient learning rather than a quick smoke baseline.

### RLPD
- Reinforcement learning from prior data.
- Prior-data quality matters: RL-generated trajectories are usually less multimodal than human or motion-planning demonstrations.
- Good for discussions about mixing prior data with online learning.

## Practical reminders

- Keep benchmark comparisons on the same observation, control, and backend contract.
- Treat WandB as a common results path, not a universal prerequisite.
- Do not auto-launch large sweeps.
- When a baseline depends on a specific demo source, state whether that source was RL-generated, motion-planned, or human-collected.

## Cross-reference

If you need the exact evaluation contract, read `references/evaluation.md`. If you need data-generation helper context, read `references/data-generation.md`.
