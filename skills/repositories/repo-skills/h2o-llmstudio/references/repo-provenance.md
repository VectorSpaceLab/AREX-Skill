# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of H2O LLM Studio. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, refresh the repo skill before relying on fine details.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T18:31:04Z",
  "repository": {
    "name": "h2o-llmstudio",
    "remote_url": "https://github.com/h2oai/h2o-llmstudio.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "d0f8b93c83b4563935bff3025f4a8a0360e8284e",
    "working_tree": "clean-before-skill-generation",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "h2o-llmstudio",
      "version": "1.15.0-dev",
      "import_names": ["llm_studio"]
    }
  ],
  "evidence": {
    "source_roots": ["llm_studio"],
    "docs": ["README.md", "documentation/docs"],
    "examples": ["examples/example_oasst2.yaml"],
    "tests": ["tests"],
    "configs": ["llm_studio/python_configs", "tests/integration/*_cfg.yaml"],
    "templates": ["model_cards", "prompts"],
    "scripts": ["distributed_train.sh", "entrypoint.sh", "llm_studio/train.py", "llm_studio/prompt.py", "llm_studio/publish_to_hugging_face.py"],
    "patches": ["patches/deepspeed-0.17.5-df-parse.patch"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the snapshot commit, treat the skill as potentially stale.
- If package metadata, problem types, CLI flags, config dataclasses, data format rules, model-card/prompt templates, or public runtime commands changed, refresh even on the same branch.
- If the current checkout is dirty in source/config/docs/runtime files and those changes affect public workflows, refresh before giving precise commands.
- If only local experiment outputs, datasets, caches, or generated skill review artifacts changed, the skill usually remains usable.
