# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of FlashRAG. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-skill-from-repo`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-21T00:00:00Z",
  "repository": {
    "name": "FlashRAG",
    "remote_url": "https://github.com/RUC-NLPIR/FlashRAG",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "e0e73399ce8d4563397b5fb4980de72a9c5e15a6",
    "working_tree": "clean-before-skill-generation",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "flashrag_dev",
      "version": "0.3.0.dev0",
      "import_names": ["flashrag"]
    }
  ],
  "evidence": {
    "source_roots": ["flashrag"],
    "docs": ["README.md", "README_zh.md", "docs", "docs/rag_failure_modes_and_debug_checklist.md"],
    "examples": ["examples/quick_start", "examples/methods", "examples/run_refiner.py", "examples/multi_turn.py", "examples/run_mm"],
    "scripts": ["scripts/build_index.sh", "scripts/chunk_doc_corpus.py", "scripts/preprocess_wiki.py"],
    "tests": ["tests/.gitkeep"],
    "configs": ["flashrag/config/basic_config.yaml", "examples/methods/my_config.yaml", "examples/run_mm/my_config.yaml", "webui/webui_configs"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and run `refresh-skill-from-repo`.
- If the working tree has public source, docs, examples, scripts, config, or package metadata changes not represented here, refresh the skill.
- If package metadata, optional extras, public factories, pipeline names, metric names, or CLI arguments changed even on the same commit, refresh the skill.
- If only DisCo review artifacts changed outside the runtime skill directory, the runtime skill is not stale for FlashRAG usage.
