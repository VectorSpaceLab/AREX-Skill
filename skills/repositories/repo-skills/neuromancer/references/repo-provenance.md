# Repository Provenance

## Purpose

Read this before deciding whether the operating skill matches a current
NeuroMANCER checkout. If the commit, package version, dirty state, or major
evidence paths differ, run a refresh workflow before relying on detailed API
claims.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-20T00:00:00Z",
  "repository": {
    "name": "neuromancer",
    "remote_url": "https://github.com/pnnl/neuromancer",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "e9456ffa090637266b18bfbc78b0c2d6d5f7bd28",
    "working_tree": "dirty",
    "dirty_paths": ["skills/ (generated operating skill and review artifacts)"],
    "source_changes_before_generation": "none observed"
  },
  "packages": [
    {
      "name": "neuromancer",
      "version": "1.5.6",
      "import_names": ["neuromancer"]
    }
  ],
  "evidence": {
    "source_roots": ["src/neuromancer"],
    "docs": ["README.md", "INSTALLATION.md", "USER_GUIDE.md", "docs"],
    "examples": ["examples/tutorials", "examples/parametric_programming", "examples/ODEs", "examples/PDEs", "examples/DAEs", "examples/SDEs", "examples/control", "examples/domain_examples", "examples/function_encoder", "examples/KANs", "examples/lightning_integration_examples"],
    "tests": ["tests", "tests/psl", "tests/slim"],
    "configs": ["pyproject.toml", "linux_env.yml", "windows_env.yml", "osxarm64_env.yml"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, treat this skill as
  potentially stale.
- If source files, public entry points, package metadata, or selected evidence
  paths changed, refresh the relevant routes even when the commit is unchanged.
- The generated `skills/` tree is an output change and is not itself evidence
  that package source changed.
