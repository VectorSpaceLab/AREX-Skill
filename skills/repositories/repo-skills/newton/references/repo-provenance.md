# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a Newton checkout. If the current commit, dirty state, package version, public API, dependency extras, examples, or docs differ from this snapshot, run a repo-skill refresh before relying on version-sensitive details.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T16:44:54Z",
  "repository": {
    "name": "newton",
    "remote_url": "https://github.com/newton-physics/newton.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "7bb6d02d8eeab2cffc3adfa453ddd63799a2ac6a",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "newton",
      "version": "1.6.0.dev0",
      "import_names": ["newton"]
    },
    {
      "name": "warp-lang",
      "version": "1.16.0",
      "import_names": ["warp"]
    }
  ],
  "evidence": {
    "source_roots": ["newton/", "newton/_src/"],
    "public_modules": [
      "newton/__init__.py",
      "newton/actuators.py",
      "newton/controllers.py",
      "newton/geometry.py",
      "newton/ik.py",
      "newton/math.py",
      "newton/selection.py",
      "newton/sensors.py",
      "newton/solvers.py",
      "newton/usd.py",
      "newton/utils.py",
      "newton/viewer.py"
    ],
    "docs": ["README.md", "docs/guide/", "docs/concepts/", "docs/solvers/", "docs/integrations/", "docs/api/"],
    "examples": ["newton/examples/"],
    "tests": ["newton/tests/"],
    "configs": ["pyproject.toml", "uv.lock", ".python-version", "AGENTS.md"]
  },
  "verification_summary": {
    "environment_status": "ok",
    "base_import": "passed",
    "warp_cpu_smoke": "passed",
    "warp_cuda_allocation_smoke": "passed",
    "minimal_newton_xpbd_cpu_smoke": "passed",
    "optional_extras_installed": []
  },
  "import_status": "not-imported-by-user-request"
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale.
- If public modules, `pyproject.toml` extras, example CLI behavior, docs concept pages, or solver/importer APIs changed, refresh even on the same branch.
- If optional dependency support changes for Python, CUDA, USD, MuJoCo, RTX, Torch, or notebook workflows, refresh the install/backend reference.
- Generated skill files under `skills/` were the only dirty paths recorded during construction; ignore them when comparing source evidence unless the task is to refresh this generated skill itself.
