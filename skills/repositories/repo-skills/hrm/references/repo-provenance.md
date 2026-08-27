# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of HRM.
If the current repo commit, dirty state, package dependency stack, or major
evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-12T16:17:18Z",
  "repository": {
    "name": "HRM",
    "remote_url": "https://github.com/sapientinc/HRM.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "ac15626f8db096a63c775b84c9dc868776a6feda",
    "working_tree": "clean-excluding-generated-skills",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "hrm-source-tree",
      "version": null,
      "import_names": [
        "dataset",
        "models",
        "puzzle_dataset",
        "pretrain",
        "evaluate",
        "utils"
      ]
    },
    {
      "name": "torch",
      "version": "2.12.0",
      "import_names": ["torch"]
    },
    {
      "name": "flash-attn",
      "version": "2.8.3",
      "import_names": ["flash_attn"]
    },
    {
      "name": "adam-atan2",
      "version": "0.0.3",
      "import_names": ["adam_atan2", "adam_atan2_backend"]
    }
  ],
  "evidence": {
    "source_roots": ["models", "dataset", "utils", "puzzle_dataset.py", "pretrain.py", "evaluate.py"],
    "docs": ["README.md"],
    "examples": ["README.md run commands", "arc_eval.ipynb", "puzzle_visualizer.html"],
    "tests": [],
    "configs": ["config/cfg_pretrain.yaml", "config/arch/hrm_v1.yaml"],
    "scripts": ["dataset/build_arc_dataset.py", "dataset/build_sudoku_dataset.py", "dataset/build_maze_dataset.py"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as
  potentially stale and run `refresh-repo-skill`.
- If the current working tree has source/config/docs changes beyond generated
  `skills/` artifacts, run `refresh-repo-skill`.
- If HRM changes its default architecture identifiers, dataset schema,
  `pretrain.py`/`evaluate.py` CLI semantics, or required CUDA dependencies, run
  `refresh-repo-skill`.
- If a future environment uses substantially different PyTorch/FlashAttention
  behavior, re-run bounded CUDA and model-forward smokes before relying on
  backend-sensitive guidance.
