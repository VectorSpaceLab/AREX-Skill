# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of PyFlux. If the current commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T13:22:32Z",
  "repository": {
    "name": "pyflux",
    "remote_url": "https://github.com/RJT1990/pyflux.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "297f2afc2095acd97c12e827dd500e8ea5da0c0f",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "pyflux",
      "version": "0.4.17",
      "import_names": ["pyflux"]
    }
  ],
  "evidence": {
    "source_roots": [
      "pyflux",
      "pyflux/arma",
      "pyflux/garch",
      "pyflux/gas",
      "pyflux/ssm",
      "pyflux/var",
      "pyflux/gpnarx",
      "pyflux/families",
      "pyflux/inference"
    ],
    "docs": [
      "README.md",
      "docs/source/index.rst",
      "docs/source/getting_started.rst",
      "docs/source/arima.rst",
      "docs/source/garch.rst",
      "docs/source/gas.rst",
      "docs/source/gas_rank.rst",
      "docs/source/ssm.rst",
      "docs/source/var.rst",
      "docs/source/gpnar.rst",
      "docs/source/classical.rst",
      "docs/source/bayes.rst",
      "docs/source/families.rst"
    ],
    "tests": [
      "pyflux/arma/tests",
      "pyflux/garch/tests",
      "pyflux/gas/tests",
      "pyflux/ssm/tests",
      "pyflux/var/tests",
      "pyflux/gpnarx/tests"
    ],
    "scripts": [
      "tools/cythonize.py"
    ],
    "package_metadata": [
      "setup.py",
      "requirements.txt",
      "requirements-dev.txt",
      "pyflux/__init__.py"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, treat the skill as potentially stale.
- If PyFlux package metadata or public exports change, refresh the skill even on the same commit.
- If generated skill output under `skills/` is the only untracked change in a checkout, ignore it for source staleness; compare the package/source evidence paths instead.
- If native tests stop matching the documented API signatures or the package starts supporting newer Python stacks, refresh the install/troubleshooting guidance.
