# Repository Provenance

## Purpose

Read this before deciding whether this LitGPT skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, public entry points, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-22T15:00:00Z",
  "repository": {
    "name": "litgpt",
    "remote_url": "https://github.com/Lightning-AI/litgpt",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "a650062da1a3c252cea6ec42ecc832225ff63ad6",
    "working_tree": "clean-at-initial-snapshot",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "litgpt",
      "version": "0.5.12",
      "import_names": ["litgpt"]
    }
  ],
  "evidence": {
    "source_roots": ["litgpt"],
    "docs": ["README.md", "tutorials"],
    "examples": ["tutorials/full_finetune_example.py", "tutorials/examples/ptl-trainer"],
    "tests": ["tests"],
    "configs": ["config_hub"],
    "extensions": ["extensions/thunder", "extensions/xla"],
    "package_metadata": ["pyproject.toml"]
  }
}
```

## Evidence Summary

- Source roots: `litgpt/` for public APIs, CLI entry points, generation/chat, training, data, conversion, evaluation, serving, model/config/tokenizer/prompt utilities, and bundled scripts.
- Public docs: `README.md` and `tutorials/` for installation, quick start, inference, fine-tuning, pretraining, dataset prep, evaluation, deployment, quantization, OOM, and Python API guidance.
- Configs: `config_hub/` for finetune and pretrain recipe patterns.
- Optional backends: `extensions/thunder` and `extensions/xla` as optional workflow evidence, not required baseline dependencies.
- Tests: `tests/` for behavior evidence and native verification candidates across CLI/API/config/data/generate/chat/finetune/pretrain/convert/evaluate/serve.

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the checkout was dirty before skill generation, or current dirty paths include package, docs, config, test, or CLI changes not represented here, run `refresh-repo-skill`.
- If `pyproject.toml`, console script names, optional dependency groups, `litgpt/__main__.py`, `litgpt/parser_config.py`, or public workflow docs changed, run `refresh-repo-skill`.
- If package version or public API signatures differ from the recorded `0.5.12` inspection, run `refresh-repo-skill`.
