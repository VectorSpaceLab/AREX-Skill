# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of POT. If the current repo commit, dirty state, package version, public API surface, examples, tests, or package metadata differ from this snapshot, run `refresh-repo-skill` before relying on this skill for version-sensitive work.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T09:14:23Z",
  "repository": {
    "name": "POT",
    "remote_url": "https://github.com/PythonOT/POT.git",
    "vcs": "git",
    "branch": "master",
    "tag": "0.9.7.post1",
    "commit": "9932112dbb0c985f3e57e38977ecc44c02f5ffc0",
    "working_tree": "clean-before-skill-generation",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "POT",
      "version": "0.9.7.post1",
      "import_names": ["ot"]
    }
  ],
  "evidence": {
    "source_roots": [
      "ot",
      "ot/batch",
      "ot/bregman",
      "ot/bsp",
      "ot/gromov",
      "ot/gnn",
      "ot/lp",
      "ot/partial",
      "ot/sliced",
      "ot/solvers",
      "ot/unbalanced"
    ],
    "docs": [
      "README.md",
      "docs/source/user_guide.rst",
      "docs/source/all.rst",
      "docs/source/index.rst"
    ],
    "examples": [
      "examples",
      "examples/backends",
      "examples/barycenters",
      "examples/domain-adaptation",
      "examples/gaussian_gmm",
      "examples/gromov",
      "examples/lowrank",
      "examples/others",
      "examples/sliced-wasserstein",
      "examples/unbalanced-partial"
    ],
    "tests": [
      "test",
      "test/batch",
      "test/gromov",
      "test/sliced",
      "test/unbalanced"
    ],
    "packaging": [
      "pyproject.toml",
      "setup.py",
      "setup.cfg",
      "MANIFEST.in",
      ".github/requirements_no_backend.txt",
      ".github/requirements_doctests.txt",
      ".github/workflows/build_tests.yml"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from the snapshot commit, treat the skill as potentially stale.
- If the package version in `ot.__version__` differs from `0.9.7.post1`, refresh the skill.
- If public solver signatures, optional extras, source module layout, examples, or CI dependency variants change, refresh the skill even on the same commit.
- Generated skill files are not source evidence drift by themselves.
