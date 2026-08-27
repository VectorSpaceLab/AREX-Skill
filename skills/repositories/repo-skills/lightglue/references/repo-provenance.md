# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T19:53:57Z",
  "repository": {
    "name": "LightGlue",
    "remote_url": "https://github.com/cvg/LightGlue.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "eb42fee2d71449efb0aa5c10549752b5d75384d8",
    "working_tree": "dirty-generated-artifacts-only",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "lightglue",
      "version": "0.0",
      "import_names": ["lightglue"]
    }
  ],
  "evidence": {
    "source_roots": ["lightglue/"],
    "docs": ["README.md"],
    "examples": ["demo.ipynb"],
    "scripts": ["benchmark.py"],
    "assets": ["assets/*.jpg", "assets/*.png", "assets/*.svg"],
    "metadata": ["pyproject.toml", "requirements.txt", "LICENSE"],
    "tests": []
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If package metadata, public exports, extractor defaults, matcher presets, or runtime dependencies changed, run `refresh-repo-skill`.
- If `benchmark.py`, `demo.ipynb`, or the public README workflows changed, refresh this skill before relying on benchmark or image-pair recipes.
- This snapshot was generated while the repository had generated `skills/` artifacts present; changes inside `skills/` alone do not imply the LightGlue package source changed.
