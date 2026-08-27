# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of Lightning-Hydra-Template. If the current repo commit, dirty state, package metadata, entry points, or major evidence paths differ from this snapshot, run `refresh-repo-skill` before relying on the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T08:23:54Z",
  "repository": {
    "name": "lightning-hydra-template",
    "remote_url": "https://github.com/ashleve/lightning-hydra-template.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "bddbc24b82ab6ccfa6243e815a49dc5bfe8d4144",
    "working_tree_at_source_capture": "clean",
    "dirty_paths_at_source_capture": []
  },
  "packages": [
    {
      "name": "src",
      "version": "0.0.1",
      "import_names": ["src"],
      "console_scripts": ["train_command", "eval_command"]
    }
  ],
  "evidence": {
    "source_roots": ["src", "configs"],
    "docs": ["README.md"],
    "examples": ["scripts/schedule.sh"],
    "tests": ["tests"],
    "configs": ["configs"],
    "metadata": ["setup.py", "requirements.txt", "environment.yaml", "pyproject.toml", "Makefile", ".github/workflows/test.yml"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale.
- If package metadata no longer names the distribution/import root as `src`, or if console scripts no longer resolve to `src.train:main` and `src.eval:main`, refresh the skill.
- If `configs/`, `src/train.py`, `src/eval.py`, `src/data/`, `src/models/`, or the pytest fixture structure changed materially, refresh the skill.
- Generated skill and review files under `skills/` were not source evidence for this snapshot.
