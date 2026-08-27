# RoboTwin bundled workspace bootstrap

Use the bundled `scripts/robotwin_workspace.py` entry point when the user does not already have a RoboTwin workspace or when they want a reproducible, pinned public checkout plus optional public assets/data.

## What it can do

- Print a manifest of the public source/data artifacts used by the generated skill.
- Bootstrap a pinned RoboTwin workspace from the public repository.
- Initialize and pin `XPolicyLab` when requested.
- Run a read-only prerequisite check.
- Download and extract public RoboTwin assets.
- Download and normalize public RoboTwin trajectories.
- Dispatch collection and evaluation commands through the bootstrapped workspace.

## Typical commands

Run these from the generated `robotwin/` skill directory, or replace `scripts/robotwin_workspace.py` with its absolute path.

```bash
# Show the manifest without mutating anything
python scripts/robotwin_workspace.py manifest

# Create a pinned public RoboTwin workspace
python scripts/robotwin_workspace.py bootstrap \
  --workspace /path/to/robotwin-workspace \
  --with-xpolicylab

# Validate prerequisites in that workspace
python scripts/robotwin_workspace.py check \
  --workspace /path/to/robotwin-workspace

# Download public assets and normalize them under the workspace
python scripts/robotwin_workspace.py download-assets \
  --workspace /path/to/robotwin-workspace

# Download public trajectories
python scripts/robotwin_workspace.py download-data \
  --workspace /path/to/robotwin-workspace \
  adjust_bottle beat_block_hammer

# Dispatch a collection command
python scripts/robotwin_workspace.py collect \
  --workspace /path/to/robotwin-workspace \
  --task-name beat_block_hammer \
  --task-config demo_clean \
  --gpu-id 0

# Dispatch an evaluation command
python scripts/robotwin_workspace.py eval \
  --workspace /path/to/robotwin-workspace -- \
  multitask --config env_cfg/eval/all_tasks.yml --dry-run
```

## Dry-run behavior

- Omit `--execute` to print the commands the helper would run.
- Add `--execute` only after you have confirmed the workspace path and are willing to let the helper mutate that workspace or download public assets/data.
- The helper never imports the full RoboTwin source tree just to print usage; it can be used as the first step from the generated skill alone.
- The `--workspace` target may be absent or an empty directory; non-empty non-git paths are rejected to avoid clobbering unrelated files.

## When to use it

- The user has no RoboTwin checkout yet.
- The workspace exists but needs to be pinned to a known public revision.
- You want to validate that the required directories and optional `XPolicyLab` pieces are present before running a more specific sub-skill.
- You want the generated skill to stay self-contained without depending on the original construction checkout.
