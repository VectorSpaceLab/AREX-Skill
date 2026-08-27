# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of Kaolin. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T17:44:38Z",
  "repository": {
    "name": "kaolin",
    "remote_url": "https://github.com/NVIDIAGameWorks/kaolin.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "d52da9f86d460e8abcd99037e21ff0bec57997ed",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ],
    "dirty_note": "Only generated skill/review artifacts were observed as untracked during creation; package source paths outside skills/ were clean."
  },
  "packages": [
    {
      "name": "kaolin",
      "version": "0.18.0",
      "import_names": ["kaolin"]
    }
  ],
  "evidence": {
    "source_roots": ["kaolin"],
    "docs": ["README.md", "docs/notes", "docs/modules"],
    "examples": ["examples/recipes", "examples/tutorial"],
    "tests": ["tests/python/kaolin", "tests/samples"],
    "scripts": ["kaolin/experimental/dash3d/kaolin-dash3d", "tools"],
    "configs": ["setup.py", "version.txt", "tools/requirements.txt", "tools/viz_requirements.txt", "tools/build_requirements.txt"]
  },
  "verification_context": {
    "installed_distribution": "official kaolin 0.18.0 wheel for torch 2.8.0 CUDA 12.8",
    "source_overlay_note": "Current source modules were also inspected through a temporary overlay with the wheel extension because the checkout includes APIs newer than the installed wheel exports."
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree dirty paths outside generated skill/artifact directories differ from this snapshot, run `refresh-repo-skill`.
- If package metadata, public entry points, CUDA/PyTorch compatibility, or source APIs such as Gaussian splat modules changed, run `refresh-repo-skill`.
- If a future installed wheel lacks APIs described here, verify whether the task targets the source checkout, the released wheel, or an unreleased branch before proceeding.
