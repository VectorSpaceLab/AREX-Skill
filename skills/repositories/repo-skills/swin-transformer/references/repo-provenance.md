# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of Swin-Transformer. If the current repository commit, dirty state, config layout, public entry scripts, or model APIs differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T18:52:32Z",
  "repository": {
    "name": "Swin-Transformer",
    "remote_url": "https://github.com/microsoft/Swin-Transformer.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "f82860bfb5225915aca09c3227159ee9e1df874d",
    "working_tree": "dirty-generated-artifacts-only",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": ["config", "models", "data", "optimizer", "lr_scheduler", "utils", "utils_simmim", "utils_moe"]
    }
  ],
  "evidence": {
    "source_roots": ["models", "data", "config.py", "main.py", "main_simmim_pt.py", "main_simmim_ft.py", "main_moe.py", "optimizer.py", "lr_scheduler.py", "utils.py", "utils_simmim.py", "utils_moe.py", "logger.py"],
    "docs": ["README.md", "get_started.md", "MODELHUB.md"],
    "examples": [],
    "tests": ["kernels/window_process/unit_test.py"],
    "configs": ["configs/swin", "configs/swinv2", "configs/swinmlp", "configs/swinmoe", "configs/simmim"],
    "optional_native_code": ["kernels/window_process"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, treat this skill as potentially stale.
- If source files under `models/`, `data/`, `config.py`, `main*.py`, `utils*.py`, `optimizer.py`, `lr_scheduler.py`, `configs/`, or `kernels/window_process/` changed, refresh.
- If dependency expectations changed from PyTorch/timm/YACS-style scripts to a packaged distribution or new CLI, refresh.
- Skill-generated files under `skills/` are recorded as dirty generated artifacts and are not themselves evidence that source behavior changed.
