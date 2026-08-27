# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T12:12:04Z",
  "repository": {
    "name": "numpyro",
    "remote_url": "https://github.com/pyro-ppl/numpyro.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "26cc211aacab08288f13b7370f9cffdc1ccc7388",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "numpyro",
      "version": "0.21.0",
      "import_names": ["numpyro"]
    }
  ],
  "evidence": {
    "source_roots": ["numpyro/"],
    "docs": ["README.md", "docs/source/"],
    "examples": ["examples/", "notebooks/source/"],
    "tests": ["test/"],
    "package_metadata": ["pyproject.toml"],
    "scripts": ["scripts/", "Makefile"],
    "ci": [".github/workflows/ci.yml"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree has source or documentation changes beyond generated skill/artifact files under `skills/`, run `refresh-repo-skill`.
- If package metadata, public API entry points, optional dependencies, examples, or tests changed even on the same commit, run `refresh-repo-skill`.
- If NumPyro's installed version differs materially from `0.21.0`, check release notes and refresh before relying on exact signatures.
