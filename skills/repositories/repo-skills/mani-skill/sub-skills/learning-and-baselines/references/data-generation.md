# Data-Generation Helpers

These helpers are used to produce benchmark datasets and rollout artifacts that feed ManiSkill's RL/IL baseline ecosystem. They are reference-only here: do not treat them as automatic training launchers.

## Helper inventory

| Helper family | Purpose | Safe note |
| --- | --- | --- |
| IL replay helper | Replays compressed demonstrations into standardized state/vision datasets used by the imitation-learning benchmark | This is the canonical replay path, but it may use GPU PhysX and large parallel counts. Lower parallelism if memory is tight. |
| Demo-oriented workflow launcher | Higher-level demonstration workflow orchestration | Treat as a reference entry point, not an auto-run helper. |
| RL-to-demo helper | Uses RL to generate successful demonstrations from dense rewards | Heavy and expensive; keep it reference-only unless the user explicitly wants to run it. |
| Motion-planning helper | Generates motion-planning demonstrations for tasks with solutions | Task-specific and often long-running; reference only. |
| RL post-processing helper | Post-processes RL outputs into benchmark-ready trajectory files | Use this as a planning reference for the post-processing stage, not as a generic replay explanation. |

## Practical reminders

- The IL benchmark helpers standardize observation and controller settings so benchmarked datasets are comparable.
- Some helpers use GPU simulation and may require more GPU memory than a small smoke run.
- If a helper needs fewer worker processes, reduce `--num-procs` instead of changing the benchmark contract.
- Keep the details of trajectory replay, HDF5 layout, and teleoperation in the trajectories-and-datasets sub-skill.

## When to use this file

Use this reference when the user asks where benchmark datasets come from, which helper produced them, or how the baseline ecosystem separates data generation from training and evaluation.
