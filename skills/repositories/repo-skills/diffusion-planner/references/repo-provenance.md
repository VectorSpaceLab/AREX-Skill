# Repository Provenance

## Purpose

Read this before deciding whether the generated skill still matches a
Diffusion Planner checkout. If the commit, dirty paths, package version, public
entry points, or major evidence paths differ, run a repository-skill refresh.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-21T21:13:48Z",
  "repository": {
    "name": "Diffusion-Planner",
    "remote_url": "https://github.com/ZhengYinan-AIR/Diffusion-Planner.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "a3a621f0b724c5fa6447f7a2fbaf9e0387bd35df",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "diffusion_planner",
      "version": "1.0.0",
      "import_names": ["diffusion_planner"]
    }
  ],
  "evidence": {
    "source_roots": [
      "diffusion_planner",
      "diffusion_planner/data_process",
      "diffusion_planner/model",
      "diffusion_planner/planner",
      "diffusion_planner/utils"
    ],
    "docs": ["README.md", "diffusion_planner/model/guidance/documentation_guidance.md"],
    "examples": ["data_process.sh", "torch_run.sh", "sim_diffusion_planner_runner.sh", "sim_guidance_demo.sh", "run_nuboard.ipynb"],
    "tests": [],
    "configs": ["diffusion_planner/config", "normalization.json", "nuplan_train.json"],
    "metadata": ["setup.py", "requirements_torch.txt"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, treat the skill as
  stale and refresh it.
- This baseline was generated from a dirty checkout because the generated
  `skills/` tree is untracked. If other dirty paths appear, review them before
  trusting source-backed claims.
- Refresh when package metadata, planner/config targets, model input shapes,
  public launch templates, or guidance call contracts change.
- The external nuPlan-devkit and dataset are construction/runtime prerequisites,
  not part of this repository snapshot; changes to those dependencies can also
  require environment re-verification.
