# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the RF-DETR repository. If the current repo commit, dirty state, package metadata, public entry points, or major evidence paths differ from this snapshot, run `refresh-repo-skill` before relying on this skill for precise API or contribution guidance.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-13T17:36:25Z",
  "repository": {
    "name": "rf-detr",
    "remote_url": "https://github.com/roboflow/rf-detr.git",
    "vcs": "git",
    "branch": "develop",
    "tag": null,
    "commit": "c4b8f4d037f541cf4b0f27f1ae4045ff31ca995f",
    "working_tree": "clean-before-skill-generation",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "rfdetr",
      "version": "1.10.0.dev0",
      "import_names": ["rfdetr"]
    }
  ],
  "evidence": {
    "source_roots": ["src/rfdetr"],
    "docs": ["README.md", "docs"],
    "configs": ["configs"],
    "tests": ["tests"],
    "package_metadata": ["pyproject.toml"],
    "contributor_metadata": ["AGENTS.md", ".github/CONTRIBUTING.md", ".github/copilot-instructions.md", ".github/workflows", ".pre-commit-config.yaml"],
    "existing_repo_skills": ["skills/rf-detr.log"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, treat this skill as potentially stale.
- If package version, public imports, console entry points, optional extras, model classes, config fields, or docs/examples/tests changed, refresh even if the commit line above is still reachable.
- If the checkout contains dirty changes outside generated skill/review artifacts, refresh before using repository-development guidance for precise contribution work.
- If RF-DETR Plus package behavior changed, refresh the optional dependency and model-overview references.

## Evidence boundaries

This skill distilled public source, docs, tests, configs, package metadata, and CI/contribution rules. It intentionally does not include private environment details, local Python paths, local package installation locations, downloaded model caches, or benchmark data artifacts.
