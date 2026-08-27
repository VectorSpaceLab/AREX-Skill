# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a TorchRL checkout. If the current repo commit, dirty state, package version, public entry points, or major evidence paths differ from this snapshot, run `refresh-repo-skill` before relying on this skill for new work.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T18:44:08Z",
  "repository": {
    "name": "pytorch-rl",
    "remote_url": "https://github.com/pytorch/rl.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "a46e872e036e9d9485f45f5bef67295ac1f5637f",
    "working_tree": "clean-before-skill-generation",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "torchrl",
      "version": "0.14.0+ga46e872",
      "import_names": ["torchrl"]
    }
  ],
  "evidence": {
    "metadata": ["pyproject.toml", "setup.py", "version.txt", "MANIFEST.in", "pytest.ini"],
    "source_roots": ["torchrl"],
    "docs": ["README.md", "docs/source/index.rst", "docs/source/reference"],
    "tutorials": ["tutorials/sphinx-tutorials"],
    "examples": ["examples"],
    "algorithm_recipes": ["sota-implementations", "sota-check"],
    "tests": ["test"],
    "knowledge_base": ["knowledge_base"],
    "ci_and_policy": ["AGENTS.md", "CONTRIBUTING.md", ".github/workflows/test-linux.yml", ".github/unittest"]
  },
  "generated_skill": {
    "id": "torchrl",
    "root_files": ["SKILL.md", "references/repo-provenance.md", "references/repo-routing-metadata.json"],
    "sub_skills": [
      "envs-and-transforms",
      "collectors-and-replay",
      "modules-and-policies",
      "objectives-and-training",
      "llm-vla-and-services",
      "development-and-testing"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the snapshot commit, treat this skill as potentially stale.
- If package metadata, console entry points, optional extras, public APIs, docs reference pages, or source layout changed materially, refresh even on the same branch.
- If a future checkout has uncommitted source changes that affect the requested workflow, inspect those changes before using this skill's cached API and troubleshooting guidance.
- Generated skill artifacts themselves are not source evidence for TorchRL APIs; use the evidence paths above when refreshing.
