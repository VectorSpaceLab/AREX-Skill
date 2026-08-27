# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of AXLearn. If the current repo commit, dirty state, package metadata, entry points, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T23:26:47Z",
  "repository": {
    "name": "axlearn",
    "remote_url": "https://github.com/apple/axlearn.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "34aed43c1b6e581c4753d06d7cbeedd5010ef26b",
    "working_tree": "dirty-untracked-generated-skill-output",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "axlearn",
      "version": "0.0.1.dev1+g34aed43c1",
      "import_names": ["axlearn"]
    }
  ],
  "evidence": {
    "source_roots": ["axlearn"],
    "docs": ["README.md", "docs/01-start.md", "docs/02-concepts.md", "docs/03-cli.md", "docs/04-infrastructure.md", "docs/05-Goodput-Monitoring.md"],
    "configs": ["pyproject.toml", ".axlearn/axlearn.default.config"],
    "core_training": ["axlearn/common", "axlearn/experiments/logistic_regression", "axlearn/experiments/test_utils.py", "axlearn/experiments/text/train_spm.py"],
    "language_models": ["axlearn/experiments/text/common.py", "axlearn/experiments/text/gpt"],
    "cli_cloud": ["axlearn/cli", "axlearn/cloud/common", "axlearn/cloud/gcp"],
    "vision": ["axlearn/vision", "axlearn/experiments/vision"],
    "audio_asr": ["axlearn/audio", "axlearn/experiments/audio/conformer"],
    "tests": ["axlearn/common/*_test.py", "axlearn/cli/*_test.py", "axlearn/cloud/**/*_test.py", "axlearn/vision/*_test.py", "axlearn/audio/*_test.py", "axlearn/experiments/**/*_test.py"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from the commit above, treat this skill as potentially stale.
- If package metadata, optional dependency groups, CLI entry points, or trainer catalog names changed, refresh this skill.
- If the current checkout has meaningful source changes outside generated skill artifacts, refresh this skill before relying on precise API claims.
