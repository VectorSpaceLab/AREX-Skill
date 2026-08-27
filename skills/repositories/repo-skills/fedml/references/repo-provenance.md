# Repository Provenance

## Purpose

Read this before deciding whether this skill matches a checkout of FedML. If the current commit, branch, dirty state, package version, or evidence paths differ materially from this snapshot, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T12:41:59Z",
  "repository": {
    "name": "FedML",
    "remote_url": "omitted-private-or-unknown",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "03e11dfee69a458a9820ec4e05b531a5f935eb2b",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "fedml",
      "version": "0.8.30",
      "import_names": ["fedml"]
    }
  ],
  "evidence": {
    "source_roots": ["python/fedml"],
    "docs": ["README.md", "python/README.md", "python/fedml/cli/README.md", "installation/README.md"],
    "examples": ["python/examples"],
    "tests": ["python/tests/smoke_test", "python/tests/test_model_cli", "python/tests/test_fedml_mlops_log", "python/tests/test_pip_init", "python/tests/test_scheduler_matcher"],
    "configs": ["python/examples/train/llm_train/job.yaml", "python/examples/launch/*.yaml", "python/examples/federate/**/*.yaml", "python/fedml/config"]
  }
}
```

## Refresh Check

- If the checkout commit changes, refresh this skill.
- If the working tree becomes dirty or the selected evidence paths change materially, refresh this skill.
- If package metadata, CLI commands, or public import surfaces change, refresh this skill.
