# Repository Provenance

Read this before deciding whether the skill matches a FastVideo checkout. If the
commit, package version, public entry points, or evidence families differ,
refresh the repo skill before relying on detailed behavior.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-28T00:30:00Z",
  "repository": {
    "name": "FastVideo",
    "remote_url": "https://github.com/hao-ai-lab/FastVideo",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "8208536cd1db7a1d32b68aaa6a679953ae23ab8b",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "fastvideo",
      "version": "0.2.0",
      "import_names": ["fastvideo"]
    }
  ],
  "evidence": {
    "source_roots": ["fastvideo", "fastvideo/api", "fastvideo/entrypoints", "fastvideo/pipelines", "fastvideo/train", "fastvideo/training", "fastvideo/eval"],
    "docs": ["README.md", "docs/getting_started", "docs/inference", "docs/design/server_contracts", "docs/training", "docs/distillation", "docs/attention", "docs/utilities"],
    "examples": ["examples/inference", "examples/serving", "examples/train", "examples/distill", "examples/datasets"],
    "tests": ["fastvideo/tests/api", "fastvideo/tests/entrypoints", "fastvideo/tests/dataset", "fastvideo/tests/train", "fastvideo/tests/eval", "fastvideo/tests/performance"],
    "configs": ["pyproject.toml", "examples/train/configs", "scripts/inference"]
  }
}
```

## Refresh check

- Compare `git rev-parse HEAD` with the snapshot commit.
- Compare package metadata and public entry points, especially `VideoGenerator`,
  `GenerationRequest`, `GeneratorConfig`, and the `fastvideo` CLI.
- If the checkout is dirty or major evidence paths changed, refresh before
  asserting model IDs, defaults, backend support, or training behavior.
- This file records relative evidence paths only; the skill does not require
  the original checkout to remain available at runtime.
