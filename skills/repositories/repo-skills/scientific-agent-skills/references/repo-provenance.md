# Repository Provenance

## Purpose

Read this before deciding whether this generated repo skill is current for a checkout of `K-Dense-AI/scientific-agent-skills`. If the current repo commit, dirty state, package metadata, CI workflows, scanner scripts, or test contracts differ from this snapshot, refresh this repo skill before relying on it for maintenance work.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T17:26:16Z",
  "repository": {
    "name": "scientific-agent-skills",
    "remote_url": "https://github.com/K-Dense-AI/scientific-agent-skills.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "d661d27ef4ddad5b9287bdd84887ace27e2320b8",
    "working_tree": "dirty-before-generation",
    "dirty_paths": [
      "skills/scientific-agent-skills.log"
    ]
  },
  "packages": [
    {
      "name": "scientific-agent-skills",
      "version": "2.62.0",
      "import_names": [],
      "notes": "Repository metadata distribution for a skill collection; no public Python package API was selected for this maintainer skill."
    }
  ],
  "evidence": {
    "source_roots": [
      "skills/",
      "tests/_contract/",
      "tests/_meta/",
      "scan_pr_skills.py",
      "scan_skills.py"
    ],
    "docs": [
      "AGENTS.md",
      "CONTRIBUTING.md",
      "README.md",
      "SECURITY.md",
      "docs/skills.md",
      "docs/security-triage.md"
    ],
    "tests": [
      "tests/_meta/test_repo_contract.py",
      "tests/conftest.py",
      "tests/run_all.py",
      "tests/skill-requirements.toml"
    ],
    "configs": [
      "pyproject.toml",
      ".github/workflows/skill-spec-validation.yml",
      ".github/workflows/skill-tests.yml",
      ".github/workflows/pr-skill-scan.yml",
      ".github/workflows/security-scan.yml",
      ".github/workflows/release.yml"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale.
- If `pyproject.toml`, `AGENTS.md`, `CONTRIBUTING.md`, `tests/_contract/`, `tests/_meta/`, `tests/run_all.py`, `tests/skill-requirements.toml`, `scan_pr_skills.py`, `scan_skills.py`, or the CI workflows changed, refresh before using this skill for PR-critical guidance.
- If the repository changes where generated DisCo repo skills or review artifacts should live, refresh before creating new outputs.
- If a future checkout gains or removes diagram-generation tooling, refresh the `skill-authoring` catalog/diagram guidance.
