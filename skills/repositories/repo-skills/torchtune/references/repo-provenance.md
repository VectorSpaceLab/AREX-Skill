# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of torchtune. If the current repo commit, dirty state, package version, public CLI/config registry, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-24T00:00:00Z",
  "repository": {
    "name": "torchtune",
    "remote_url": "https://github.com/meta-pytorch/torchtune",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "bd2a0fc7c31430972728494fa01aaeeb0ebf1ba1",
    "working_tree": "clean-before-skill-generation",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "torchtune",
      "version": "0.7.0",
      "installed_metadata_version_observed": "0.0.0",
      "import_names": ["torchtune"]
    }
  ],
  "entry_points": {
    "console_scripts": ["tune"]
  },
  "evidence": {
    "source_roots": ["torchtune"],
    "recipes": ["recipes", "recipes/configs"],
    "docs": ["README.md", "docs/source"],
    "tests": ["tests"],
    "configs": ["pyproject.toml", "recipes/configs"],
    "scripts": ["recipes/*.py", "recipes/dev/*.py", "recipes/*.slurm", "recipes/dev/*.sbatch"],
    "ci_and_maintenance": ["CONTRIBUTING.md", ".github/workflows"]
  },
  "inspection_facts": {
    "public_imports_verified": [
      "torchtune",
      "torchtune.config",
      "torchtune.data",
      "torchtune.datasets",
      "torchtune.generation",
      "torchtune.models",
      "torchtune.modules",
      "torchtune.training",
      "torchtune.rlhf",
      "torchtune.utils"
    ],
    "recipe_registry_count": 22,
    "recipes_package_import": "intentionally-raises",
    "top_level_import_requires": ["torchao"],
    "known_current_code_issue": "torchtune.rlhf.loss import fails in this checkout because dpo.py references missing typing/dataclass imports"
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree has non-DisCo changes in `torchtune/`, `recipes/`, `docs/source/`, `tests/`, `pyproject.toml`, or `README.md`, run `refresh-repo-skill`.
- If `tune --help`, `torchtune._recipe_registry.get_all_recipes()`, public model/dataset exports, or recipe configs differ from the facts above, refresh before relying on command or API guidance.
- If package metadata starts reporting a concrete version different from `version.txt`, refresh the package/version notes.
