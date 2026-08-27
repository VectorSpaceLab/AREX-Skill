# Troubleshooting

| Surface | Likely cause | What to do | Source cues |
| --- | --- | --- | --- |
| Missing baseline dependencies | Optional extras were never installed | Check the family-specific notes before assuming a command should work. Common extras include torch ecosystem packages for faster PPO paths, JAX for RFCL-like workflows, and family-specific environment files for model-based baselines. | Baseline docs and family notes |
| WandB/login assumptions | The official results may use WandB, but local runs may not be logged | Say whether WandB is required or optional. Do not assume the user has logged in or has network access. | Baseline docs and results links |
| Dataset / replay mismatch | The benchmarked IL datasets were not replayed with the canonical replay settings | Use the documented replayed datasets for benchmark comparisons. If you are not using the standard replay pipeline, call out the deviation. | IL docs and data-generation notes |
| Backend mismatch | Data were collected on a different simulator backend than training/evaluation | Keep the data-collection backend and the learning backend aligned when fairness matters, especially for precise tasks. State the mismatch explicitly if you cannot align them. | IL setup notes and baseline family notes |
| Demo length too short for the policy | Slow demonstrations hit the default episode limit before the policy can succeed | Increase the episode limit, often to about 2x the mean demo length for BC/ACT/DP-style training. | BC/ACT/DP notes |
| Long-running training or sweeps | The user asked for the full benchmark run instead of a bounded plan | Treat the training command sets as reference material. Start with one task or the small benchmark set and avoid auto-launching a large sweep. | Baseline command inventories |
| External repository / download dependency | Some families are built around external dependencies or datasets | Mention the external clone or download requirement before promising a working command. Do not present the workflow as self-contained if it is not. | Family notes and data-generation helpers |
| Visual training memory pressure | RGB / RGBD baselines use large buffers or image tensors | Lower image resolution, number of envs, or buffer size before scaling the benchmark. Visual variants are especially sensitive to memory. | PPO/SAC visual notes |

## Algorithm-specific reminders

- PPO may not solve every task: some tasks do not yet have dense rewards or are too hard for standard PPO.
- RGBD-style SAC is documented for modest image sizes only.
- Diffusion Policy is currently documented as tuned for state and RGB, not the most complex visual stacks.
- RFCL-style flows are often described without a GPU-vectorized ManiSkill path.
- Prior-data methods work best when the prior data are not too multimodal.
- TD-MPC2 evaluation needs the checkpoint's `control_mode` and `num_eval_envs` to match the training setup when those are not default.

## If the request still looks expensive

Stop and ask whether the user wants a reference-only plan, a single-task command family, or a full training run. Do not silently convert a planning request into a long benchmark execution.
