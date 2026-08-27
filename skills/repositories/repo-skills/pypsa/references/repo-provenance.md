# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a PyPSA checkout. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T14:26:40Z",
  "repository": {
    "name": "PyPSA",
    "remote_url": "https://github.com/PyPSA/PyPSA.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "6d1da8049b3346969bc8f2b97f7835dc0b7c6fbe",
    "working_tree": "dirty-generated-skill-artifacts",
    "dirty_paths": [
      "skills/disco/pypsa/"
    ],
    "dirty_note": "Source code evidence was otherwise taken from the commit above; the working tree was dirty because generated runtime skill and non-runtime review artifacts were being written during distillation."
  },
  "packages": [
    {
      "name": "pypsa",
      "version": "0.0.post1.dev1+g6d1da8049",
      "import_names": ["pypsa"],
      "version_note": "The shallow Git snapshot did not include tags, so setuptools-scm resolved a development version for inspection."
    }
  ],
  "evidence": {
    "source_roots": [
      "pypsa/",
      "pypsa/data/"
    ],
    "docs": [
      "README.md",
      "docs/home/installation.md",
      "docs/user-guide/",
      "docs/api/"
    ],
    "examples": [
      "docs/examples/",
      "examples/networks/"
    ],
    "tests": [
      "test/"
    ],
    "configs": [
      "pyproject.toml",
      "uv.lock",
      "mkdocs.yml",
      ".github/workflows/test.yml"
    ],
    "existing_repo_skills": [
      "skills/PyPSA.log"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, treat the skill as potentially stale and run `refresh-repo-skill`.
- If public package metadata, dependencies, optional extras, or entry points change, refresh this skill even on the same commit.
- If `pypsa.Network`, `n.optimize`, `n.pf`, I/O method signatures, statistics accessors, plotting accessors, clustering accessors, or Components API behavior changes, refresh the relevant sub-skills.
- If a future checkout has a clean tag-resolved package version, update this provenance during refresh.
