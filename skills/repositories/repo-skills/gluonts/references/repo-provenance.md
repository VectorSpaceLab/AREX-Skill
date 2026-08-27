# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T17:12:00Z",
  "repository": {
    "name": "gluonts",
    "remote_url": "https://github.com/awslabs/gluonts.git",
    "vcs": "git",
    "branch": "dev",
    "tag": null,
    "commit": "889a3df86a89a365880b4bc1488bcf4c039f265e",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "gluonts",
      "version": "0.18.0.dev0",
      "import_names": ["gluonts"]
    }
  ],
  "evidence": {
    "source_roots": [
      "src/gluonts/core",
      "src/gluonts/dataset",
      "src/gluonts/transform",
      "src/gluonts/time_feature",
      "src/gluonts/model",
      "src/gluonts/torch",
      "src/gluonts/evaluation",
      "src/gluonts/ev",
      "src/gluonts/shell",
      "src/gluonts/ext",
      "src/gluonts/zebras"
    ],
    "docs": [
      "README.md",
      "docs/getting_started",
      "docs/tutorials/data_manipulation",
      "src/gluonts/shell/README.md"
    ],
    "examples": [
      "examples/evaluate_model.py",
      "examples/persist_model.py",
      "examples/warm_start.py",
      "examples/dockerfiles"
    ],
    "tests": [
      "test/dataset",
      "test/transform",
      "test/time_feature",
      "test/model",
      "test/torch",
      "test/evaluation",
      "test/ev",
      "test/shell",
      "test/ext"
    ],
    "configs": ["pyproject.toml", "Justfile"]
  },
  "selected_scope_notes": {
    "required_backends": ["cpu"],
    "optional_backends": ["cuda", "external adapters"],
    "not_selected_as_verified_required": ["src/gluonts/mx", "src/gluonts/nursery", "optional extension runtimes"]
  }
}
```

The checkout was clean before generated skill output was written. Skill files under `skills/` are generated artifacts, not source evidence for the package snapshot above.

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If source files, package metadata, docs, examples, or tests listed in `evidence` changed, run `refresh-repo-skill` even if the commit is the same.
- If optional dependency groups, PyTorch estimator exports, shell CLI behavior, or evaluation APIs changed, refresh the skill.
- If a user needs MXNet workflows, optional external adapters, or service deployment beyond the selected scope, prepare and verify that environment before extending this skill.
