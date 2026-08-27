---
name: simulation-environments
description: "Guides researchers through RoboCasa installation gates, Gymnasium
  and robosuite environment construction, seeded simulation, observations and
  actions, rendering, and bounded rollouts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# RoboCasa simulation environments

Use this route when the task is to install or diagnose RoboCasa, construct a
`robosuite` or Gymnasium environment, choose a `pretrain`/`target`/`all` split,
understand reset-step data, check seed behavior, render, or run a short random
rollout. Read the focused references before writing environment code:

- [API reference](references/api-reference.md) — compatibility gates, `Kitchen`,
  `create_env`, the Gym wrapper, split semantics, and action/observation keys.
- [Workflows](references/workflows.md) — install/import checks, construction,
  deterministic probes, render configuration, and bounded video rollouts.
- [Troubleshooting](references/troubleshooting.md) — duplicate keyword errors,
  missing external XML/object assets, backend problems, and action mismatches.
- [Safe diagnostic](scripts/check_install.py) — run from any working directory
  with no download; it reports package gates, optional assets, and render
  signals. Use `--help` first and `--require-assets` only when a full reset is
  intended.

## Fast route

1. Install the pinned RoboCasa dependencies and public `robosuite >=1.5.2` as
   described in [Workflows](references/workflows.md). Import `robocasa` only
   after the exact MuJoCo and NumPy gates pass.
2. Run `python path/to/check_install.py --json` (or invoke the bundled script
   from this skill directory) to separate package readiness from downloaded
   asset readiness. The checkout may import successfully while a reset fails
   because the large kitchen fixture/object downloads are absent.
3. For the supported Gym recipe, import `robocasa` before `gym.make`, use an
   explicit supported split (`pretrain`, `target`, or `all`), and let
   `create_env` own `use_camera_obs` and `has_offscreen_renderer`. Do **not**
   pass either of those two keywords again through `kwargs`.
4. Validate the action dictionary against the exact keys in the API reference;
   do not mix the flat 12-value `convert_action` input with a Gym action dict.
5. Keep rollouts bounded by `num_steps`. `create_env` deliberately sets
   `ignore_done=True`; a requested `horizon` is therefore not a replacement for
   an outer rollout bound unless the lower-level API is used directly.

## Scope boundaries

This route owns simulation lifecycle and package/backend behavior. Route task
catalogs, scene/layout/style selection, fixture/object availability, and asset
validation through the root skill's `tasks-scenes-assets` route. Route dataset
schemas/playback through `datasets-demonstrations`, and teleoperation or
collection through `teleoperation-and-collection`. Use the root skill as the
cross-sub-skill router: [root RoboCasa skill](../../SKILL.md).

## Verification status

Package import, exact version assertions, and API/signature inspection were
verified for RoboCasa 1.0.1 with MuJoCo 3.3.1, NumPy 2.2.5, robosuite 1.5.2,
Gymnasium 0.29.1, h5py 3.16.0, and LeRobot 0.3.3. RoboCasa registers 374
kitchen environments. A direct `create_env` constructor succeeds in the
inspection setup, but reset is not a full simulation pass without the
external fixture/object assets; do not claim reset, stepping, rendering, or
video success merely from import or constructor success. MimicGen is optional
and was not installed.
