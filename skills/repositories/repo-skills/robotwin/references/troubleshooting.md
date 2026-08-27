# RoboTwin global troubleshooting

## Which sub-skill owns the failure?

| Symptom | Go to |
| --- | --- |
| SAPIEN, MPLib, renderer, task import, `Base_Task`, action helper, robot/camera config, planning failure | [simulation-core](../sub-skills/simulation-core/SKILL.md) |
| Missing HDF5 keys, wrong data layout, download/extract failure, legacy conversion issue, empty instruction sidecars | [data-pipeline](../sub-skills/data-pipeline/SKILL.md) |
| XPolicyLab submodule/policy adapter missing, scheduler config rejected, remote server unavailable, action-shape error | [policy-eval](../sub-skills/policy-eval/SKILL.md) |
| Task template placeholders, `play_once()` info mismatch, credential-bound generation, generated code review | [task-authoring](../sub-skills/task-authoring/SKILL.md) |

## Common cross-cutting failures

### RoboTwin is not importable as a package

This revision is source-tree oriented and lacks package metadata. Run commands from a RoboTwin workspace and set the workspace root on `PYTHONPATH` only when programmatic imports are needed. Do not try to solve this by installing the generated skill; the skill is documentation and helper scripts, not the RoboTwin package.

### NumPy ABI mismatch

If SAPIEN/MPLib/OpenCV imports fail or compiled modules complain about NumPy, re-pin to `numpy==1.26.4` and rerun `python -m pip check`. Some dependency installs may upgrade NumPy; re-pin after installing SAPIEN/OpenCV/Open3D if needed.

### Assets absent

If importing `envs` fails with a missing object metadata JSON, download/extract RoboTwin assets before task work. A tiny render smoke can pass before assets, but `load_actors()` and cluttered-table utilities need the asset tree.

### XPolicyLab absent

If evaluation commands fail before scheduling jobs, initialize `XPolicyLab`. Do not assume an empty submodule directory is usable.

### Long/side-effectful commands

Downloads, self-collection, policy rollouts, LeRobot conversion, and credentialed generation can be expensive or mutate state. Prefer dry-runs, one-task smoke tests, bundled validators, and explicit user approval before scaling.

## Safe escalation order

1. Run a read-only validator or `--dry-run` first.
2. Check configuration and file layout before reinstalling dependencies.
3. Check assets/submodules before debugging task code.
4. Narrow to one task, one episode, one GPU, and `render_freq: 0`.
5. Only after a tiny smoke passes, scale to all tasks or multi-GPU evaluation.
