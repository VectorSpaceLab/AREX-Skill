# Benchmark Task Sets

ManiSkill's baseline docs describe benchmark task sets for both reinforcement learning and learning from demonstrations. The public pages are evolving, so use the current docs as the source of truth instead of older comments or scripts.

## RL benchmark summary

- The RL baselines page describes a **small set** for lower-compute benchmarking and a **large set** for broader coverage.
- Both sets are described with **state-based and visual-based** settings.
- The benchmark tasks use **normalized dense rewards**.
- The page says the small set is intended for researchers without large compute budgets.
- The page also says the large set is still being developed and tested.

### Current explicit small-set IDs on the public page

- `PushCube-v1`
- `PickCube-v1`
- `PegInsertionSide-v1`
- `PushT-v1`
- `HumanoidPlaceAppleInBowl-v1`
- `AnymalC-Reach-v1`
- `OpenCabinetDrawer-v1`

> Note: the same page states that the small benchmark contains 8 tasks, but the visible markdown currently enumerates 7 IDs and leaves the broader candidate list in comments. Do not hard-code the set without rechecking the page when you need an exact benchmark inventory.

### How to use the set

- Start with the small set when you want a compute-light orientation pass.
- Treat the large set as a broader research benchmark, not as a default quick smoke.
- Keep observation mode, control mode, backend, and evaluation protocol fixed when comparing results.

## IL benchmark summary

- The IL docs standardize benchmark datasets by replaying compressed demonstration trajectories into fixed observation/control settings.
- The public IL benchmark scripts are designed to produce comparable state-based and vision-based datasets.
- The benchmarked results on the ManiSkill WandB project use the replayed datasets from the documented helper script.
- If you are not using the benchmarked replay pipeline, call out the deviation explicitly.

## Task-set selection reminders

- Use the small set for a quick sanity check or low-budget comparison.
- Use the larger benchmark only when the question really needs it.
- If a task has randomizable object geometry, evaluation should reconfigure on reset so the benchmark stays fair.
- For demo-driven baselines, remember that demo source quality matters as much as task ID selection.

## Cross-reference

If you need the exact evaluation contract, read `references/evaluation.md`. If you need data-generation shell helper context, read `references/data-generation.md`.
