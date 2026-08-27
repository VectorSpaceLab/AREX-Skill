# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the
repository. If the current repo commit, dirty state, package version, or major
evidence paths differ from this snapshot, run a repo-skill refresh workflow.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-13T17:46:15Z",
  "repository": {
    "name": "umap",
    "remote_url": "https://github.com/lmcinnes/umap.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "e82ed0d457b566b043ef44f4007a7149b0daca74",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "umap-learn",
      "version": "0.5.12",
      "import_names": ["umap"]
    }
  ],
  "evidence": {
    "source_roots": ["umap/"],
    "metadata": ["pyproject.toml", "setup.py"],
    "docs": ["README.rst", "doc/"],
    "examples": ["examples/"],
    "tests": ["umap/tests/"],
    "excluded": ["benchmarks/", "ci_scripts/", "doc/images/", "images/", "notebooks/ as runtime dependencies", "skills/ generated files"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from the recorded commit, treat the skill as
  potentially stale and refresh it.
- If the current dirty paths differ materially from the recorded `skills/`
  production files, refresh before relying on source-level details.
- If `pyproject.toml`, public APIs under `umap/`, docs under `doc/`, or tests
  under `umap/tests/` changed, refresh even if package version did not change.
- If optional dependency behavior for `plot` or `parametric_umap` changed,
  refresh the affected sub-skill.
