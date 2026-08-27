# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of ExecuTorch. If the commit, package metadata, or major evidence paths differ, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T03:09:27Z",
  "repository": {
    "name": "executorch",
    "remote_url": "https://github.com/pytorch/executorch.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "42ebbc3d63e60135518e3120f3908940abfae081",
    "working_tree": "dirty-generated-skills-only",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "executorch",
      "version": "1.5.0+42ebbc3",
      "import_names": [
        "executorch"
      ]
    }
  ],
  "evidence": {
    "source_roots": [
      "src/executorch",
      "exir",
      "export",
      "runtime",
      "extension",
      "backends",
      "devtools"
    ],
    "docs": [
      "README.md",
      "README-wheel.md",
      "docs/source"
    ],
    "examples": [
      "examples"
    ],
    "tests": [
      "test",
      "exir/tests",
      "export/tests",
      "runtime/test",
      "backends/*/test*"
    ],
    "configs": [
      "pyproject.toml",
      "setup.py",
      "CMakeLists.txt",
      "CMakePresets.json",
      "Makefile"
    ],
    "repo_local_agent_guidance": [
      ".claude/skills",
      ".wiki"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale.
- If source files, package metadata, backend APIs, CMake presets, or public examples changed, refresh even on the same branch.
- The recorded dirty path is the generated `skills/` output from this production run, not an ExecuTorch source-code modification.

