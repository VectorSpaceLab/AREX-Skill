# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-24T00:00:00Z",
  "repository": {
    "name": "anndata",
    "remote_url": "https://github.com/scverse/anndata",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "e176a68de95e72d66ccb0061d301dffc0e349f8c",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "anndata",
      "version": "0.1.0.dev1+ge176a68de",
      "import_names": ["anndata"]
    }
  ],
  "evidence": {
    "source_roots": ["src/anndata"],
    "docs": ["README.md", "docs/api.md", "docs/concatenation.rst", "docs/accessors.rst", "docs/fileformat-prose.md", "docs/tutorials/zarr-v3.md", "docs/interoperability.md", "docs/typing.md"],
    "tests": ["tests", "src/anndata/tests"],
    "metadata": ["pyproject.toml"],
    "existing_skills": ["skills/anndata", "skills/disco/anndata", "skills/disco/anndata-2"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree dirty paths differ from `repository.dirty_paths`, check whether the changes affect public APIs, docs, examples, tests, or dependency metadata before trusting this skill.
- If package metadata, public exports, optional extras, or storage behavior changed even on the same commit, run `refresh-repo-skill`.
