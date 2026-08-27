# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a FunClip checkout.
If the current repo commit, dirty state, package version, public entry points, or
major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T06:20:15Z",
  "repository": {
    "name": "FunClip",
    "remote_url": "https://github.com/modelscope/FunClip.git",
    "vcs": "git",
    "branch": "main",
    "tag": "v2.1.1",
    "commit": "6eab789b3920afecaa08280cd824049482c354df",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ],
    "dirty_note": "skills/ was untracked during generation and contains production log plus generated skill/review artifacts."
  },
  "packages": [
    {
      "name": "FunClip source checkout",
      "version": "2.1.1",
      "import_names": [
        "launch",
        "videoclipper",
        "llm",
        "utils"
      ],
      "entry_points": [
        "python funclip/launch.py",
        "python funclip/videoclipper.py"
      ]
    }
  ],
  "evidence": {
    "source_roots": [
      "funclip/"
    ],
    "docs": [
      "README.md",
      "README_zh.md",
      "docs/releases/v2.1.1.md",
      "CONTRIBUTING.md"
    ],
    "tests": [
      "tests/"
    ],
    "scripts": [
      "scripts/build_release_assets.py",
      "funclip/test/test.sh",
      "funclip/test/imagemagick_test.py"
    ],
    "configs_and_metadata": [
      "requirements.txt",
      "VERSION",
      ".github/workflows/tests.yml",
      ".github/workflows/release.yml",
      ".github/ISSUE_TEMPLATE/",
      ".github/PULL_REQUEST_TEMPLATE.md"
    ],
    "excluded_large_or_nonruntime_paths": [
      "font/STHeitiMedium.ttc",
      "docs/images/",
      ".git/"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the snapshot commit, treat this skill as
  potentially stale and refresh it.
- If the checkout is dirty in source or docs outside generated skill artifacts,
  inspect the changed paths and refresh if user-facing behavior may differ.
- If `VERSION`, `requirements.txt`, `funclip/launch.py`, `funclip/videoclipper.py`,
  any `funclip/llm/*.py` provider helper, release workflow, or public tests
  changed, refresh the affected sub-skill.
- If a future checkout becomes package-installable or changes import style, refresh
  the install/runtime guidance because this skill is based on the current
  script-oriented import surface.
