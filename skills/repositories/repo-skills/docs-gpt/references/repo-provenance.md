# Repository Provenance

## Purpose

Use this snapshot to decide whether the DocsGPT skill still matches the current checkout. Refresh the skill when the checked-out commit, project version, or relevant repository surfaces differ.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-17T16:24:17Z",
  "repository": {
    "name": "DocsGPT",
    "remote_url": "https://github.com/arc53/DocsGPT.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "ff5bc01d20430b52d9028f71ebcaaa34c1a6b8e0",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ]
  },
  "project": {
    "name": "DocsGPT",
    "version": "0.18.0",
    "version_source": "application/version.py"
  },
  "evidence": {
    "version_files": [
      "application/version.py"
    ],
    "runtime_roots": [
      "application/app.py",
      "application/asgi.py",
      "application/core/settings.py"
    ],
    "frontend_and_docs": [
      "frontend/package.json",
      "docs/package.json"
    ],
    "deployment_and_tests": [
      "deployment/",
      "tests/"
    ]
  }
}
```

## Evidence

The snapshot was captured from the DocsGPT checkout containing this skill:

- `git remote get-url origin` returned `https://github.com/arc53/DocsGPT.git`.
- `git branch --show-current` returned `main`.
- `git rev-parse HEAD` returned `ff5bc01d20430b52d9028f71ebcaaa34c1a6b8e0`.
- `git describe --tags --exact-match HEAD` found no exact tag, so `tag` is `null`.
- `git status --porcelain=v1` reported the generated `skills/` tree as untracked, so the checkout is recorded as dirty without implying source-code modifications.
- `application/version.py` defines `__version__ = "0.18.0"`; this is the canonical backend/project version used by the skill.

## Refresh Check

- If the current origin, branch, or full commit differs from the snapshot, treat repository facts in the skill as potentially stale.
- If `application/version.py` no longer reports `0.18.0`, refresh version-sensitive guidance.
- Refresh the relevant focused skill when API routes, ASGI mounts, settings, storage services, authentication, frontend commands, extensions, or test layouts change, even if the version string does not.
