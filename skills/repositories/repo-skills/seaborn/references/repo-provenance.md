# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of seaborn. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T18:53:05Z",
  "repository": {
    "name": "seaborn",
    "remote_url": "https://github.com/mwaskom/seaborn.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "f04b6cd5484267a0885d1fed068e99dff3a1b226",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "seaborn",
      "version": "0.14.0.dev0",
      "import_names": ["seaborn"]
    }
  ],
  "evidence": {
    "source_roots": ["seaborn", "seaborn/_core", "seaborn/_marks", "seaborn/_stats"],
    "docs": ["README.md", "doc/README.md", "doc/installing.rst", "doc/faq.rst", "doc/api.rst", "doc/tutorial.yaml"],
    "examples": ["examples"],
    "tests": ["tests"],
    "configs": ["pyproject.toml", "Makefile"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and this snapshot was clean, or the snapshot was dirty and the current dirty paths differ, run `refresh-repo-skill`.
- If package metadata, public import modules, optional dependency groups, file-format APIs, database/application wrappers, or interface modules changed even on the same commit, run `refresh-repo-skill`.
- The package version above records the wheel used for live API smoke checks; the repository source/docs/tests named above were also used as evidence for current checkout coverage.
