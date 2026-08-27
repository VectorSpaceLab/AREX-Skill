# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the
Diffusion Policy repository. If the current commit, package metadata, public
entrypoints, configs, or major evidence paths differ from this snapshot, refresh
this repo skill before relying on it for new work.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T03:55:13Z",
  "repository": {
    "name": "diffusion_policy",
    "remote_url": "https://github.com/real-stanford/diffusion_policy.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "5ba07ac6661db573af695b419a7947ecb704690f",
    "working_tree": "clean-before-skill-generation",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "diffusion_policy",
      "version": "0.0.0",
      "import_names": ["diffusion_policy"]
    }
  ],
  "evidence": {
    "source_roots": ["diffusion_policy"],
    "docs": ["README.md"],
    "examples": ["demo_pusht.py", "demo_real_robot.py"],
    "entrypoints": ["train.py", "eval.py", "eval_real_robot.py", "ray_train_multirun.py", "multirun_metrics.py", "ray_exec.py"],
    "tests": ["tests"],
    "configs": ["diffusion_policy/config", "image_pusht_diffusion_policy_cnn.yaml"],
    "environment_files": ["conda_environment.yaml", "conda_environment_macos.yaml", "conda_environment_real.yaml"],
    "runtime_script_evidence": ["diffusion_policy/scripts"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from the recorded commit, treat this skill as
  potentially stale and refresh it.
- If `setup.py`, dependency environment files, public entrypoint names, config
  targets, dataset/policy/workspace class names, or real-robot command-line
  options changed, refresh even if the commit comparison is inconclusive.
- If a checkout was generated from a dirty source tree with source-code changes
  outside generated skill outputs, refresh and record the changed paths.

## Packaging Note

The repository metadata declares distribution name `diffusion_policy` but does
not install console scripts. The upstream training/evaluation commands are
script-style project entrypoints, so users typically run them from a checkout or
from an equivalent project that provides those entrypoints and config files.
This skill captures the command contracts and provides safe bundled inspection
helpers; it does not bundle the full training runtime or benchmark configs.
