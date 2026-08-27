---
name: isaaclab
description: "Use IsaacLab for robotics simulation, asset and sensor catalogs,
  task presets, RL wrappers, imitation learning, teleoperation, and repo tooling
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Isaac Lab

Use this repo skill when the task names IsaacLab, the `isaaclab` package, or one of the repo’s major workflow packages and scripts.

## Quick start

- Read `references/repo-provenance.md` first when checking whether this skill still matches the checkout.
- Install the standard package set with `./isaaclab.sh -i`, or install only the core packages with `./isaaclab.sh -i core`.
- Use `./isaaclab.sh -i isaacsim` when you need the Isaac Sim based stack.
- Verify the environment with:
  - `python -m pip check`
  - `python -I -c "import isaaclab, isaaclab_tasks, isaaclab_assets"`
  - `./isaaclab.sh --help`
- Use `scripts/inspect_isaaclab_install.py` for a fast install and import summary.

## Route by task

- `sub-skills/simulation-core/SKILL.md` — launch simulation, choose physics and renderer backends, use `AppLauncher`, and reason about core runtime config.
- `sub-skills/assets-and-sensors/SKILL.md` — work with `isaaclab_assets`, robot and sensor configs, and asset catalog inspection.
- `sub-skills/tasks-and-presets/SKILL.md` — list environments, resolve preset selectors, and parse task configs.
- `sub-skills/rl-training/SKILL.md` — run `train` and `play`, choose RL libraries, and load checkpoints or video runs.
- `sub-skills/imitation-and-teleop/SKILL.md` — work with Mimic, teleoperation, OpenXR/CloudXR, and retargeters.
- `sub-skills/tooling-and-deployment/SKILL.md` — maintain docs, tests, conversion tools, changelog fragments, scaffolding, and deployment helpers.

## Common commands

- `./isaaclab.sh -p ...` — run Python inside an Isaac Lab-aware environment.
- `./isaaclab.sh train ...` / `./isaaclab.sh play ...` — RL entrypoints.
- `./isaaclab.sh -t` — run tests.
- `./isaaclab.sh -f` — run formatting and lint hooks.
- `./isaaclab.sh -d` — build docs from source.
- `./isaaclab.sh -n ...` — scaffold a new project or task.
- `./isaaclab.sh -c` / `./isaaclab.sh -u` — create a new Conda or uv environment.

## Working notes

- Keep runtime guidance self-contained inside this skill tree.
- Do not rely on the original checkout after reading the bundled references.
- For install details, command semantics, and backend caveats, use `references/installation-and-cli.md` and `references/troubleshooting.md`.
