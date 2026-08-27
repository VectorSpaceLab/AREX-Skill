# Repository Provenance

Read this before deciding whether the generated skill matches a checkout of
OpenFermion. If the commit, dirty state, package version, or public evidence
paths differ materially, run the repo-skill refresh workflow.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-20T00:00:00Z",
  "repository": {
    "name": "OpenFermion",
    "remote_url": "https://github.com/quantumlib/OpenFermion",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "b9609ba8b1548eb6d9ba5e1c8a8eac5b271457df",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "openfermion",
      "version": "1.8.2.dev0",
      "import_names": ["openfermion"]
    }
  ],
  "evidence": {
    "source_roots": [
      "src/openfermion",
      "src/openfermion/ops",
      "src/openfermion/transforms",
      "src/openfermion/hamiltonians",
      "src/openfermion/chem",
      "src/openfermion/circuits",
      "src/openfermion/linalg",
      "src/openfermion/measurements",
      "src/openfermion/functionals",
      "src/openfermion/utils",
      "src/openfermion/resource_estimates"
    ],
    "docs": ["README.md", "docs/overview.md", "docs/install.md", "docs/tutorials"],
    "examples": ["docs/tutorials/*.ipynb as distilled evidence"],
    "tests": ["src/openfermion/**/*_test.py"],
    "configs": ["setup.py", "pyproject.toml", "dev_tools/requirements/deps/runtime.txt"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as
  potentially stale and run `refresh-repo-skill`.
- This snapshot was generated from a dirty checkout because the repository's
  `skills/` path contained the production log and then generated runtime and
  review artifacts. The source package commit itself was unchanged during
  construction; compare the relative dirty paths before refreshing.
- If package metadata, public exports, dependency bounds, or source roots
  change, refresh even when the commit is unchanged.
- The optional `resources` extra and external plugin packages are intentionally
  not part of the minimum core inspection baseline; changes to their public
  contracts may require a focused extension or refresh.
