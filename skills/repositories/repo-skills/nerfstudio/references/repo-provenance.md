# Repository Provenance

## Purpose

Read this before deciding whether the repo skill is current for a checkout of Nerfstudio. If the commit, package metadata, entry points, dirty state, or major evidence paths differ, refresh the skill rather than trusting its routing or defaults.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T17:22:48Z",
  "repository": {
    "name": "nerfstudio",
    "remote_url": "https://github.com/nerfstudio-project/nerfstudio.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "50e0e3c70c775e89333256213363badbf074f29d",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "nerfstudio",
      "version": "1.1.5",
      "import_names": ["nerfstudio"]
    }
  ],
  "evidence": {
    "source_roots": ["nerfstudio"],
    "docs": ["README.md", "docs/quickstart", "docs/reference", "docs/developer_guides", "docs/extensions"],
    "examples": ["colab"],
    "tests": ["tests"],
    "configs": ["pyproject.toml", "pixi.toml"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the snapshot commit, run a repo-skill refresh.
- If the checkout becomes dirty or the changed paths affect `nerfstudio/`, `docs/`, `pyproject.toml`, or selected tests, refresh before relying on this skill.
- If package version, `project.scripts`, built-in method/dataparser catalogs, or config field semantics change, refresh even if the commit is unchanged in a copied checkout.
