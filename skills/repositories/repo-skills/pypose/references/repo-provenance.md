# Repository Provenance

## Purpose

Read this before deciding whether the PyPose operating skill matches a current
package checkout. If the commit, dirty state, package version, public entry
points, or major evidence paths differ, run a refresh workflow before relying
on detailed claims.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-20T00:00:00Z",
  "repository": {
    "name": "pypose",
    "remote_url": "https://github.com/pypose/pypose.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "46786b0e554f5c5b43111ef2ac1b0aef06080763",
    "working_tree": "dirty-from-skill-generation",
    "dirty_paths": [
      "skills/disco/pypose/",
      "review artifacts outside the runtime tree"
    ]
  },
  "packages": [
    {
      "name": "pypose",
      "version": "0.9.5",
      "import_names": ["pypose"]
    }
  ],
  "evidence": {
    "source_roots": [
      "pypose/",
      "pypose/lietensor/",
      "pypose/module/",
      "pypose/optim/"
    ],
    "docs": [
      "README.md",
      "docs/source/lietensor.rst",
      "docs/source/modules.rst",
      "docs/source/optim.rst",
      "docs/source/functions.rst",
      "docs/source/convert.rst",
      "docs/source/metric.rst",
      "docs/source/autograd.rst",
      "docs/source/testing.rst",
      "docs/source/utils.rst"
    ],
    "examples": [
      "examples/lietensor/",
      "examples/module/filter/",
      "examples/module/dynamics/",
      "examples/module/mpc/",
      "examples/module/imu/",
      "examples/module/pcr/",
      "examples/module/ba/",
      "examples/module/pgo/",
      "examples/module/reprojpgo/",
      "examples/module/spline/"
    ],
    "tests": [
      "tests/lietensor/",
      "tests/basics/",
      "tests/module/",
      "tests/optim/",
      "tests/function/",
      "tests/sparse/"
    ],
    "configs": [
      "setup.py",
      "requirements/runtime.txt"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from the recorded commit, treat this skill as
  potentially stale and refresh it.
- If the current working tree is clean or the generated dirty paths differ from
  the snapshot, refresh the provenance and affected workflow guidance.
- If package metadata, PyTorch requirements, public exports, optional BAE
  integration, or the module/optimizer signatures change, refresh the affected
  sub-skill even when the commit is unchanged.
- The generated skill intentionally records only relative evidence paths and
  public package facts; it does not require the source checkout to remain
  available at runtime.
