---
name: robotwin
description: "Use RoboTwin bimanual manipulation simulation, data, task
  authoring, and XPolicyLab policy-evaluation workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# RoboTwin

Use this repo skill when a user asks about RoboTwin 2.0, dual-arm/bimanual manipulation simulation, RoboTwin task configs/classes, demonstration data collection, XPolicyLab-format trajectories, or XPolicyLab policy evaluation for RoboTwin.

## Start here

1. If the user already has a RoboTwin workspace, work there. If not, use the bundled [workspace bootstrapper](references/workspace-bootstrap.md) to materialize a pinned public workspace and public assets without depending on the construction checkout.
2. Check setup before long runs: Python 3.10/3.11, NumPy 1.x ABI, SAPIEN/MPLib/Open3D/PyTorch dependencies, downloaded assets, and initialized `XPolicyLab` submodule when evaluating policies.
3. Route to the smallest sub-skill below. Return here for cross-cutting install, assets, provenance, and global troubleshooting.

## Sub-skill routes

| User intent | Read |
| --- | --- |
| Understand `Base_Task`, task classes, SAPIEN scene setup, action helpers, robot/camera configs, render smoke, or planning failures | [simulation-core](sub-skills/simulation-core/SKILL.md) |
| Download pre-collected data, collect demonstrations, validate XPolicyLab HDF5, understand data layouts, or convert legacy raw episodes | [data-pipeline](sub-skills/data-pipeline/SKILL.md) |
| Configure XPolicyLab local/remote policy evaluation, scheduler dry-runs, policy-server pools, result logs, or qpos/endpose action adapter shapes | [policy-eval](sub-skills/policy-eval/SKILL.md) |
| Add or modify tasks/configs/language templates, expand episode instructions, or reason about credential-bound LLM/code-generation utilities | [task-authoring](sub-skills/task-authoring/SKILL.md) |

## Cross-cutting references

- [repo-provenance.md](references/repo-provenance.md): source revision and evidence paths used to build this skill.
- [install-and-submodules.md](references/install-and-submodules.md): setup sequence, dependency pins, assets, and `XPolicyLab` submodule handling.
- [workspace-bootstrap.md](references/workspace-bootstrap.md): self-contained bootstrap/check/download entry point for users without a ready workspace.
- [troubleshooting.md](references/troubleshooting.md): global failures that span sub-skills.
- [repo-routing-metadata.json](references/repo-routing-metadata.json): structured router metadata for managed repo-skill import.
- [scripts/check_robotwin_prereqs.py](scripts/check_robotwin_prereqs.py): read-only workspace and dependency check before any mutating workflow.

## Bundled runtime entry points

- `scripts/robotwin_workspace.py`: self-contained bootstrapper for pinned public workspaces, asset/data download, collection dispatch, and evaluation dispatch.
- `scripts/check_robotwin_prereqs.py`: read-only environment and workspace probe for dry-run validation before any mutating workflow.

## High-level workflows

### Prepare a workspace

1. If starting from scratch, run the bundled workspace bootstrapper to create a pinned public RoboTwin checkout.
2. Create an isolated Python 3.10/3.11 environment.
3. Install the simulation/data/eval dependencies with `numpy==1.26.4`; avoid Python 3.13 for current compiled dependencies.
4. Download and extract RoboTwin assets before importing `envs` or running tasks.
5. Run a SAPIEN render smoke.
6. For policy evaluation, initialize `XPolicyLab` or use the bootstrapper's `bootstrap --with-xpolicylab` path before working on adapter workflows.

### Collect or inspect data

1. Use [data-pipeline](sub-skills/data-pipeline/SKILL.md) to choose pre-collected data vs self-collection.
2. Use [simulation-core](sub-skills/simulation-core/SKILL.md) if collection fails during task initialization, actor creation, rendering, or planning.
3. Validate HDF5 schema before feeding data to training or LeRobot conversion.
4. If you only need a standalone workspace or public asset/data acquisition flow, the bundled bootstrapper can create it without any original checkout.

### Evaluate a policy

1. Initialize `XPolicyLab` and confirm the policy adapter exists.
2. Use [policy-eval](sub-skills/policy-eval/SKILL.md) for local scheduler or remote server/client commands.
3. Run dry-runs and synthetic action-shape checks before full rollout.
4. Use [data-pipeline](sub-skills/data-pipeline/SKILL.md) for dataset layout questions and [simulation-core](sub-skills/simulation-core/SKILL.md) for environment/task failures.

## Do not assume

- Do not assume RoboTwin is pip-installable as a normal package; this source revision has no `setup.py` or `pyproject.toml`.
- Do not import top-level `envs` before assets are present; cluttered-object metadata is read during import.
- Do not treat the empty or uninitialized `XPolicyLab` directory as a usable policy stack; initialize the submodule first.
- Do not run large downloads, long collection, policy rollouts, or credentialed LLM generation unless the user asks for those side effects.
