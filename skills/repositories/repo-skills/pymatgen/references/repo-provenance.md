# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-24T00:00:00Z",
  "repository": {
    "name": "pymatgen",
    "remote_url": "https://github.com/materialsproject/pymatgen",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "78ca4b1115c6bf20e0e8107e591d11021b83b44a",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "pymatgen",
      "version": "2026.5.4",
      "import_names": ["pymatgen"]
    },
    {
      "name": "pymatgen-core",
      "version": "2026.5.18",
      "import_names": ["pymatgen.core"]
    }
  ],
  "evidence": {
    "source_roots": ["src/pymatgen"],
    "docs": ["README.md", "docs/index.md", "docs/usage.md", "docs/installation.md", "docs/compatibility.md", "docs/pymatgen.md"],
    "examples": ["examples/README.md"],
    "tests": ["tests", "test-files"],
    "configs": ["pyproject.toml"],
    "existing_repo_skill_evidence": ["skills/pymatgen/sub-skills"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and this snapshot was clean, or the snapshot was dirty and the current dirty paths differ, run `refresh-repo-skill`.
- If package metadata, optional extras, console entry points, public imports, or source evidence paths changed even on the same commit, run `refresh-repo-skill`.
