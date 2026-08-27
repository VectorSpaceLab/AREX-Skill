# RoboTwin repo provenance

## Source snapshot

- Repository: RoboTwin bimanual robotic manipulation platform.
- Public remote: `https://github.com/RoboTwin-Platform/RoboTwin.git`.
- Branch: `main`.
- Commit: `266f3aadf505a4f7fe9af0faa41a20f5f47cd123`.
- Exact tag: none detected.
- Submodule evidence: `XPolicyLab` is configured as a submodule at path `XPolicyLab`, URL `https://github.com/XPolicyLab/XPolicyLab.git`, branch `main`; this checkout reported the pinned submodule commit `c37109c500be67d0dea6b36bf7337bbd26e763cd` but the submodule contents were not initialized in the construction workspace.
- Package version: not available; this revision has no `setup.py` or `pyproject.toml` package metadata.

## Working tree state at construction

- Dirty state: generated `skills/` outputs were untracked during construction.
- Source evidence directories used for skill content were read from the checked-out repository files listed below. No source files were intentionally modified for this skill.

## Evidence paths

- `README.md`
- `.gitmodules`
- `collect_data.sh`
- `scripts/requirements.txt`
- `scripts/_install.sh`
- `scripts/test_render.py`
- `scripts/collect_data.py`
- `scripts/download_xpolicylab_data.sh`
- `scripts/process_data_xpolicylab.py`
- `scripts/eval_policy.sh`
- `scripts/eval_policy_multitask.py`
- `scripts/eval_policy_server.py`
- `scripts/eval_policy_xpolicylab.py`
- `scripts/update_xpolicylab.sh`
- `envs/_GLOBAL_CONFIGS.py`
- `envs/_base_task.py`
- representative task modules such as `envs/beat_block_hammer.py`
- `envs/robot/robot.py`
- `envs/robot/planner.py`
- `envs/camera/camera.py`
- `envs/utils/action.py`
- `envs/utils/pkl2hdf5.py`
- `envs/utils/parse_hdf5.py`
- `env_cfg/task_config/*.yml`
- `env_cfg/eval/*.yml`
- `env_cfg/*.yml`
- `description/task_instruction/*.json`
- `description/objects_description/**/*.json`
- `description/utils/generate_episode_instructions.py`
- `description/utils/generate_task_description.py`
- `description/utils/generate_object_description.py`
- `description/utils/agent.py`
- `code_gen/*.py`
- `assets/_download.py`

## Verification baseline notes

- A private construction environment verified the selected dependency imports, PyTorch CUDA allocation, and SAPIEN render smoke.
- Top-level `envs` import requires downloaded assets in this revision; missing asset metadata is documented as a setup prerequisite rather than hidden.
- XPolicyLab-specific policy scripts were documented from RoboTwin dispatcher/scheduler evidence and README usage because the submodule checkout was empty in the construction workspace.
