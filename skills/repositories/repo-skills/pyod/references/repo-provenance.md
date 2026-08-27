# Repository Provenance

## Purpose

Read this before deciding whether this PyOD repo skill is current for a checkout
of the repository. If the current repo commit, dirty state, package version,
entry points, optional extras, or major evidence paths differ from this
snapshot, refresh the skill before relying on it for new source facts.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-12T18:52:29Z",
  "repository": {
    "name": "pyod",
    "remote_url": "https://github.com/yzhao062/pyod.git",
    "vcs": "git",
    "branch": "master",
    "tag": "v3.6.4",
    "commit": "3d0169a32ab8ce68aeaf7f0bb408c281f2fb1b1e",
    "working_tree": "dirty-generated-skill-only",
    "dirty_paths": [
      "skills/disco/pyod/",
      "skills/tests/pyod/"
    ]
  },
  "packages": [
    {
      "name": "pyod",
      "version": "3.6.4",
      "import_names": ["pyod"]
    }
  ],
  "evidence": {
    "source_roots": ["pyod"],
    "models": ["pyod/models"],
    "utilities": ["pyod/utils"],
    "cli_and_services": ["pyod/cli.py", "pyod/mcp_server.py"],
    "packaged_skills": ["pyod/skills"],
    "docs": [
      "README.rst",
      "docs/install.rst",
      "docs/examples",
      "docs/model_persistence.rst",
      "docs/thresholding.rst",
      "docs/skill_maintenance.rst"
    ],
    "examples": ["examples"],
    "tests": ["pyod/test"],
    "scripts": ["scripts/regen_skill.py", "scripts/render_agentic_demo.py"],
    "package_metadata": ["pyproject.toml", "requirements.txt", "setup.py", "MANIFEST.in"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from the commit above, treat this skill as
  potentially stale and run `refresh-repo-skill`.
- If package metadata changes (dependencies, optional extras, entry points,
  package data, Python version support), refresh before using install or CLI
  guidance.
- If files under `pyod/models`, `pyod/utils`, `pyod/cli.py`, `pyod/mcp_server.py`,
  `pyod/skills`, public docs, examples, or tests change materially, refresh the
  affected sub-skill.
- The dirty paths listed above are generated skill and review artifacts from the
  construction run, not source evidence changes.
