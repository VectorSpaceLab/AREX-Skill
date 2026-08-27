# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for an Optuna checkout. If the current repository commit, dirty state, package version, public entry points, or major evidence paths differ from this snapshot, refresh the skill from repository evidence.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-21T00:00:00Z",
  "repository": {
    "name": "optuna",
    "remote_url": "https://github.com/optuna/optuna.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "243c156d9dda5093fa4358c6923fb22cd721fd04",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "optuna",
      "version": "5.0.0.dev",
      "import_names": ["optuna"],
      "console_scripts": ["optuna"]
    }
  ],
  "evidence": {
    "source_roots": ["optuna"],
    "docs": ["README.md", "docs/source"],
    "examples": ["tutorial", "docs/visualization_examples", "docs/visualization_matplotlib_examples"],
    "tests": ["tests"],
    "configs": ["pyproject.toml"],
    "excluded": [".git", ".github", "build", "dist", "docs/image", "optuna/storages/_grpc/auto_generated", "skills/tests"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run a repo-skill refresh.
- If the current working tree has changed paths outside `skills/`, refresh before trusting API or CLI details.
- If `optuna.__version__`, `pyproject.toml` dependencies, console scripts, or public APIs changed, refresh even if the commit is similar.
- Keep local environment paths, Python executables, and machine-specific setup outside public skill content.
